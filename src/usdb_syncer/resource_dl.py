"""Functions for downloading and processing media."""

import os
from enum import Enum
from typing import Union

import requests
import yt_dlp
from PIL import Image, ImageEnhance, ImageOps

from usdb_syncer.download_options import AudioOptions, VideoOptions
from usdb_syncer.logger import Log, get_logger
from usdb_syncer.meta_tags.deserializer import ImageMetaTags
from usdb_syncer.settings import Browser
from usdb_syncer.typing_helpers import assert_never
from usdb_syncer.usdb_scraper import SongDetails

# from moviepy.editor import VideoFileClip
# import subprocess

IMAGE_DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
    )
}


class ImageKind(Enum):
    """Types of images used for songs."""

    COVER = "CO"
    BACKGROUND = "BG"

    def __str__(self) -> str:  # pylint: disable=invalid-str-returned
        match self:
            case ImageKind.COVER:
                return "cover"
            case ImageKind.BACKGROUND:
                return "background"
            case _ as unreachable:
                assert_never(unreachable)


def url_from_video_resouce(resource: str) -> str:
    if "://" in resource:
        return resource
    if "/" in resource:
        return f"https://{resource}"
    return f"https://www.youtube.com/watch?v={resource}"


def download_video(
    resource: str,
    options: AudioOptions | VideoOptions,
    browser: Browser,
    path_stem: str,
    logger: Log,
) -> str | None:
    """Download video from resource to path and process it according to options.

    Parameters:
        resource: URL or YouTube id
        options: parameters for downloading and processing
        browser: browser to use cookies from
        path_stem: the target on the file system *without* an extension

    Returns:
        the extension of the successfully downloaded file or None
    """
    url = url_from_video_resouce(resource)
    ext = None
    ydl_opts: dict[str, Union[str, bool, tuple, list]] = {
        "format": options.ytdl_format(),
        "outtmpl": f"{path_stem}.%(ext)s",
        "keepvideo": False,
        "verbose": False,
    }
    if browser.value:
        ydl_opts["cookiesfrombrowser"] = (browser.value,)
    if isinstance(options, AudioOptions):
        pp_extract_audio = {
            "key": "FFmpegExtractAudio",
            "preferredquality": "320",
            "preferredcodec": options.format.value,
        }
        pp_normalize = {
            "key": "ExecAfterDownload",
            "exec_cmd": " && ".join(
                [
                    # copy to temp file
                    f'ffmpeg -i "{path_stem}.%(ext)s" '
                    f'-acodec copy -y "{path_stem}-temp.%(ext)s"',
                    # simple loudness normalization with EBU R128 algorithm
                    # see https://trac.ffmpeg.org/wiki/AudioVolume
                    f'ffmpeg -i "{path_stem}-temp.%(ext)s" '
                    f'-filter:a loudnorm -y "{path_stem}.%(ext)s"',
                ]
            ),
        }
        ydl_opts["postprocessors"] = [pp_extract_audio, pp_normalize]
        # `prepare_filename()` does not take into account postprocessing, so note the
        # file extension
        ext = options.format.value

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            filename = ydl.prepare_filename(ydl.extract_info(f"{url}"))
        except yt_dlp.utils.YoutubeDLError:
            logger.debug(f"error downloading video url: {url}")
            return None
        finally:
            # remove temp file created while normalization
            if os.path.exists(temp_file := f"{path_stem}-temp.{ext}"):
                os.remove(temp_file)

    return ext or os.path.splitext(filename)[1][1:]


def download_image(url: str, logger: Log) -> bytes | None:
    try:
        reply = requests.get(
            url, allow_redirects=True, headers=IMAGE_DOWNLOAD_HEADERS, timeout=60
        )
    except requests.RequestException:
        logger.error(
            f"Failed to retrieve {url}. The server may be down or your internet "
            "connection is currently unavailable."
        )
        return None
    if reply.status_code in range(100, 399):
        # 1xx informational response, 2xx success, 3xx redirection
        return reply.content
    if reply.status_code in range(400, 499):
        logger.error(
            f"Client error {reply.status_code}. Failed to download {reply.url}"
        )
    elif reply.status_code in range(500, 599):
        logger.error(
            f"Server error {reply.status_code}. Failed to download {reply.url}"
        )
    return None


def download_and_process_image(
    filename_stem: str,
    meta_tags: ImageMetaTags | None,
    details: SongDetails,
    pathname: str,
    kind: ImageKind,
    max_width: int | None,
) -> str | None:
    logger = get_logger(__file__, details.song_id)
    if not (url := _get_image_url(meta_tags, details, kind, logger)):
        return None
    if not (img_bytes := download_image(url, logger)):
        logger.error(f"#{str(kind).upper()}: file does not exist at url: {url}")
        return None
    fname = f"{filename_stem} [{kind.value}].jpg"
    path = os.path.join(pathname, fname)
    with open(path, "wb") as file:
        file.write(img_bytes)
    _process_image(meta_tags, max_width, path)
    return fname


def _get_image_url(
    meta_tags: ImageMetaTags | None, details: SongDetails, kind: ImageKind, logger: Log
) -> str | None:
    url = None
    if meta_tags:
        url = meta_tags.source_url()
        logger.debug(f"downloading {kind} from #VIDEO params: {url}")
    elif kind is ImageKind.COVER and details.cover_url:
        url = details.cover_url
        logger.warning(
            "no cover resource in #VIDEO tag, so fallback to small usdb cover!"
        )
    else:
        logger.warning(f"no {kind} resource found")
    return url


def _process_image(
    meta_tags: ImageMetaTags | None, max_width: int | None, path: str
) -> None:
    processed = False
    with Image.open(path).convert("RGB") as image:
        if meta_tags and meta_tags.image_processing():
            processed = True
            if rotate := meta_tags.rotate:
                image = image.rotate(rotate, resample=Image.BICUBIC, expand=True)
            if crop := meta_tags.crop:
                image = image.crop((crop.left, crop.upper, crop.right, crop.lower))
            if resize := meta_tags.resize:
                image = image.resize(
                    (resize.width, resize.height), resample=Image.LANCZOS
                )
            if meta_tags.contrast == "auto":
                image = ImageOps.autocontrast(image, cutoff=5)
            elif meta_tags.contrast:
                image = ImageEnhance.Contrast(image).enhance(meta_tags.contrast)
        if max_width and max_width < image.width:
            processed = True
            height = round(image.height * max_width / image.width)
            image = image.resize((max_width, height), resample=Image.LANCZOS)

        if processed:
            image.save(path, "jpeg", quality=100, subsampling=0)
