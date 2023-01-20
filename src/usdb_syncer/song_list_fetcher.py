"""Runnable for getting the available songs from USDB or the local cache."""

import json
import os
from glob import glob

from usdb_syncer import SongId, settings
from usdb_syncer.logger import get_logger
from usdb_syncer.song_data import LocalFiles, SongData
from usdb_syncer.song_txt import SongTxt
from usdb_syncer.sync_meta import SyncMeta
from usdb_syncer.usdb_scraper import get_usdb_available_songs
from usdb_syncer.usdb_song import UsdbSong, UsdbSongEncoder
from usdb_syncer.utils import AppPaths, try_read_unknown_encoding


def get_all_song_data(force_reload: bool) -> tuple[SongData, ...]:
    songs = get_available_songs(force_reload)
    local_files = find_local_files()
    return tuple(
        SongData.from_usdb_song(song, local_files.get(song.song_id, LocalFiles()))
        for song in songs
    )


def resync_song_data(data: tuple[SongData, ...]) -> tuple[SongData, ...]:
    local_files = find_local_files()
    return tuple(
        song.with_local_files(local_files.get(song.data.song_id, LocalFiles()))
        for song in data
    )


def get_available_songs(force_reload: bool) -> list[UsdbSong]:
    if force_reload or not (available_songs := load_available_songs()):
        available_songs = get_usdb_available_songs()
        dump_available_songs(available_songs)
    return available_songs


def load_available_songs() -> list[UsdbSong] | None:
    path = AppPaths.song_list
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf8") as file:
        try:
            return json.load(file, object_hook=UsdbSong.from_json)
        except (json.decoder.JSONDecodeError, TypeError, KeyError):
            return None


def dump_available_songs(available_songs: list[UsdbSong]) -> None:
    with open(AppPaths.song_list, "w", encoding="utf8") as file:
        json.dump(available_songs, file, cls=UsdbSongEncoder)


def find_local_files() -> dict[SongId, LocalFiles]:
    local_files: dict[SongId, LocalFiles] = {}
    pattern = os.path.join(settings.get_song_dir(), "**", "*.usdb")
    for path in glob(pattern, recursive=True):
        if meta := SyncMeta.try_from_file(path):
            local_files[meta.song_id] = files = LocalFiles(usdb_path=path)
            folder = os.path.dirname(path)
            if txt := _get_song_txt(meta, folder):
                files.txt = True
                files.audio = _file_exists(folder, txt.headers.mp3)
                files.video = _file_exists(folder, txt.headers.video)
                files.cover = _file_exists(folder, txt.headers.cover)
                files.background = _file_exists(folder, txt.headers.background)
    return local_files


def _get_song_txt(meta: SyncMeta, folder: str) -> SongTxt | None:
    if not meta.txt:
        return None
    txt_path = os.path.join(folder, meta.txt.fname)
    logger = get_logger(__file__, meta.song_id)
    if os.path.exists(txt_path) and (contents := try_read_unknown_encoding(txt_path)):
        return SongTxt.try_parse(contents, logger)
    return None


def _file_exists(folder: str, fname: str | None) -> bool:
    if not fname:
        return False
    return os.path.exists(os.path.join(folder, fname))
