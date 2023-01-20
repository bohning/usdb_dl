"""Table model for song data."""

from enum import Enum
from typing import Any, Iterator

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
)

from usdb_syncer import SongId
from usdb_syncer.gui.song_table.column import Column
from usdb_syncer.song_data import SongData
from usdb_syncer.usdb_scraper import UsdbSong

QIndex = QModelIndex | QPersistentModelIndex


class CustomRole(int, Enum):
    """Custom values expanding Qt.QItemDataRole."""

    ALL_DATA = 100
    SORT = 101


class TableModel(QAbstractTableModel):
    """Table model for song data."""

    songs: tuple[SongData, ...] = tuple()
    _rows: dict[SongId, int]

    def __init__(self, parent: QObject) -> None:
        self._rows = {}
        super().__init__(parent)

    def set_data(self, songs: tuple[SongData, ...]) -> None:
        self.beginResetModel()
        self.songs = songs
        self._rows = {song.data.song_id: idx for idx, song in enumerate(songs)}
        self.endResetModel()

    def update_item(self, new: SongData) -> None:
        idx = self._rows[new.data.song_id]
        self.songs = self.songs[:idx] + (new,) + self.songs[idx + 1 :]
        start_idx = self.index(idx, 0)
        end_idx = self.index(idx, self.columnCount())
        self.dataChanged.emit(start_idx, end_idx)  # type:ignore

    def ids_for_indices(self, indices: Iterator[QModelIndex]) -> list[SongId]:
        return [self.songs[idx.row()].data.song_id for idx in indices]

    def item_for_id(self, song_id: SongId) -> SongData | None:
        if (idx := self._rows.get(song_id)) is not None:
            return self.songs[idx]
        return None

    def all_local_songs(self) -> Iterator[UsdbSong]:
        return (song.data for song in self.songs if song.local_files.txt)

    ### QAbstractTableModel implementation

    def columnCount(self, parent: QIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(Column)

    def rowCount(self, parent: QIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.songs)

    def data(self, index: QIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.songs[index.row()].display_data(index.column())
        if role == Qt.ItemDataRole.DecorationRole:
            return self.songs[index.row()].decoration_data(index.column())
        if role == CustomRole.ALL_DATA:
            return self.songs[index.row()]
        if role == CustomRole.SORT:
            return self.songs[index.row()].sort_data(index.column())
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation != Qt.Orientation.Horizontal:
            return None
        if role == Qt.ItemDataRole.DecorationRole:
            return Column(section).decoration_data()
        if role == Qt.ItemDataRole.DisplayRole:
            return Column(section).display_data()
        return None
