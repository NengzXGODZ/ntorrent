"""
Custom item delegate that paints a real progress bar inside the Progress column
instead of plain percentage text.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionProgressBar, QStyle, QApplication
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtGui import QColor

from models import COL_PROGRESS
from ui.theme import ACCENT_CYAN, ACCENT_EMERALD


class ProgressBarDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index: QModelIndex):
        if index.column() != COL_PROGRESS:
            super().paint(painter, option, index)
            return

        row = index.data(Qt.ItemDataRole.UserRole)
        if row is None:
            super().paint(painter, option, index)
            return

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
