"""Tests for UsdbSong."""

import json

import attrs

from usdb_syncer import SongId
from usdb_syncer.usdb_song import UsdbSong, UsdbSongEncoder


def test_encoding_and_decoding_song_meta() -> None:
    song = UsdbSong(
        sample_url="",
        song_id=SongId(123),
        artist="Foo",
        title="Bar",
        genre="Pop",
        year=1999,
        language="Esperanto",
        creator="unknown",
        edition="",
        golden_notes=True,
        rating=0,
        views=1,
    )
    song_json = json.dumps(song, cls=UsdbSongEncoder)
    new_song = json.loads(song_json, object_hook=UsdbSong.from_json)
    assert isinstance(new_song, UsdbSong)
    assert attrs.asdict(song) == attrs.asdict(new_song)
