"""
QSortFilterProxyModel wrapping TorrentTableModel: lets the table be sorted
by clicking any column header, and filtered live by a name search box,
without the table model itself needing to know about either feature.
"""
from __future__ import annotations

from PyQt6.QtCore import QSortFilterProxyModel, Qt, QModelIndex

from models import (
    COL_NAME, COL_SIZE, COL_PROGRESS, COL_STATUS, COL_DOWN, COL_UP,
    COL_SEEDS, COL_PEERS, COL_ETA, COL_SAVE_PATH,
)

# Maps each column to the raw (non-formatted) value used to sort it, pulled
# straight off the TorrentSnapshot so e.g. "1.2 GB" vs "850 MB" sorts by
# actual byte count, not alphabetically by the formatted string.
_SORT_KEYS = {
    COL_NAME: lambda r: r.name.lower(),
    COL_SIZE: lambda r: r.size,
    COL_PROGRESS: lambda r: r.progress,
    COL_STATUS: lambda r: r.status,
    COL_DOWN: lambda r: r.download_rate,
    COL_UP: lambda r: r.upload_rate,
    COL_SEEDS: lambda r: r.num_seeds,
    COL_PEERS: lambda r: r.num_peers,
    COL_ETA: lambda r: r.eta_seconds if r.eta_seconds is not None else float("inf"),
    COL_SAVE_PATH: lambda r: r.save_path.lower(),
}


class TorrentFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""
        self.setDynamicSortFilter(True)

    def set_search_text(self, text: str) -> None:
        self._search_text = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._search_text:
            return True
        index = self.sourceModel().index(source_row, COL_NAME, source_parent)
        name = str(self.sourceModel().data(index, Qt.ItemDataRole.DisplayRole) or "")
        return self._search_text in name.lower()

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        row_l = self.sourceModel().data(left, Qt.ItemDataRole.UserRole)
        row_r = self.sourceModel().data(right, Qt.ItemDataRole.UserRole)
        getter = _SORT_KEYS.get(left.column())
        if row_l is None or row_r is None or getter is None:
            return super().lessThan(left, right)
        try:
            return getter(row_l) < getter(row_r)
        except TypeError:
            return super().lessThan(left, right)
