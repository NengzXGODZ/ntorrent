"""
Qt table model for the torrent list, plus small formatting helpers.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant

from engine import TorrentSnapshot

COL_NAME, COL_SIZE, COL_PROGRESS, COL_STATUS, COL_DOWN, COL_UP, \
    COL_SEEDS, COL_PEERS, COL_ETA, COL_SAVE_PATH = range(10)

HEADERS = ["Name", "Size", "Progress", "Status", "Down Speed", "Up Speed",
           "Seeds", "Peers", "ETA", "Save Path"]


def human_size(num_bytes: float) -> str:
    if num_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def human_rate(bytes_per_sec: float) -> str:
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.0f} B/s"
    return f"{human_size(bytes_per_sec)}/s"


def human_eta(seconds) -> str:
    if seconds is None:
        return "—"
    if seconds > 99 * 3600:
        return "∞"
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


class TorrentTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[TorrentSnapshot] = []

    def set_rows(self, rows: list[TorrentSnapshot]) -> None:
        # Reset wholesale; the table is small enough (hundreds of rows at most)
        # that a full reset per tick is simpler and fast enough than diffing.
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def row_at(self, row: int) -> TorrentSnapshot | None:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return HEADERS[section]
        return QVariant()

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == COL_NAME:
                return row.name
            if col == COL_SIZE:
                return human_size(row.size)
            if col == COL_PROGRESS:
                return f"{row.progress * 100:.1f}%"
            if col == COL_STATUS:
                return row.status
            if col == COL_DOWN:
                return human_rate(row.download_rate) if row.download_rate > 0 else "—"
            if col == COL_UP:
                return human_rate(row.upload_rate) if row.upload_rate > 0 else "—"
            if col == COL_SEEDS:
                return str(row.num_seeds)
            if col == COL_PEERS:
                return str(row.num_peers)
            if col == COL_ETA:
                return human_eta(row.eta_seconds)
            if col == COL_SAVE_PATH:
                return row.save_path

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (COL_SIZE, COL_PROGRESS, COL_DOWN, COL_UP, COL_SEEDS, COL_PEERS, COL_ETA):
                return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter

        if role == Qt.ItemDataRole.UserRole:
            return row

        return QVariant()
