"""
Custom item delegate for the torrent table: paints a real progress bar in
the Progress column and a colored status "pill" in the Status column,
instead of plain text for either.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionProgressBar, QStyle, QApplication
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtGui import QColor, QPainter

from models import COL_PROGRESS, COL_STATUS
from ui.theme import ACCENT_CYAN, ACCENT_EMERALD, TEXT_SECONDARY, STATUS_COLORS


class TorrentRowDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index: QModelIndex):
        if index.column() == COL_PROGRESS:
            self._paint_progress(painter, option, index)
            return
        if index.column() == COL_STATUS:
            self._paint_status_badge(painter, option, index)
            return
        super().paint(painter, option, index)

    @staticmethod
    def _fill_selection_background(painter: QPainter, option) -> None:
        # Our custom-painted columns skip the delegate's normal background
        # paint, so without this a selected row would show no highlight
        # behind the progress bar / status badge, unlike every other column.
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

    def _paint_progress(self, painter: QPainter, option, index: QModelIndex) -> None:
        row = index.data(Qt.ItemDataRole.UserRole)
        if row is None:
            super().paint(painter, option, index)
            return

        self._fill_selection_background(painter, option)

        pct = max(0.0, min(1.0, row.progress)) * 100.0

        opt = QStyleOptionProgressBar()
        opt.rect = option.rect.adjusted(4, 4, -4, -4)
        opt.minimum = 0
        opt.maximum = 100
        opt.progress = int(pct)
        opt.text = f"{pct:.1f}%"
        opt.textVisible = True
        opt.textAlignment = Qt.AlignmentFlag.AlignCenter

        color = ACCENT_EMERALD if row.is_finished else ACCENT_CYAN
        opt.palette.setColor(opt.palette.ColorRole.Highlight, QColor(color))

        style = QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ProgressBar, opt, painter)

    def _paint_status_badge(self, painter: QPainter, option, index: QModelIndex) -> None:
        row = index.data(Qt.ItemDataRole.UserRole)
        if row is None:
            super().paint(painter, option, index)
            return

        self._fill_selection_background(painter, option)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        accent = QColor(STATUS_COLORS.get(row.status, TEXT_SECONDARY))
        badge_rect = option.rect.adjusted(6, 5, -6, -5)

        bg = QColor(accent)
        bg.setAlpha(38)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(badge_rect, 7, 7)

        painter.setPen(accent)
        font = painter.font()
        font.setBold(True)
        font.setPointSizeF(max(8.0, font.pointSizeF() - 0.5))
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, row.status)

        painter.restore()


# Backwards-compatible alias (the class used to only handle the progress bar).
ProgressBarDelegate = TorrentRowDelegate
