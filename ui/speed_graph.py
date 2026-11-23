"""
Live 60-second scrolling speed graph (download/upload) built on pyqtgraph.
"""
from __future__ import annotations

from collections import deque

import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.theme import BG_PANEL, BORDER, TEXT_SECONDARY, DOWNLOAD_COLOR, UPLOAD_COLOR

WINDOW_SECONDS = 60


class SpeedGraph(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackground(BG_PANEL)
        self.showGrid(x=True, y=True, alpha=0.15)
        self.setMouseEnabled(x=False, y=False)
        self.setMenuEnabled(False)
        self.hideButtons()
        self.setMinimumHeight(140)

        axis_pen = pg.mkPen(color=BORDER, width=1)
        for axis_name in ("bottom", "left"):
            axis = self.getAxis(axis_name)
            axis.setPen(axis_pen)
            axis.setTextPen(pg.mkPen(color=TEXT_SECONDARY))

        self.setLabel("left", "Speed", units="B/s")
        self.setLabel("bottom", "Seconds ago")
        self.getPlotItem().invertX(True)
        self.addLegend(offset=(10, 6), labelTextColor=TEXT_SECONDARY)

        self._x = list(range(WINDOW_SECONDS))
        self._down_hist = deque([0.0] * WINDOW_SECONDS, maxlen=WINDOW_SECONDS)
        self._up_hist = deque([0.0] * WINDOW_SECONDS, maxlen=WINDOW_SECONDS)

        down_pen = pg.mkPen(color=DOWNLOAD_COLOR, width=2)
        up_pen = pg.mkPen(color=UPLOAD_COLOR, width=2)

        self.down_curve = self.plot(self._x, list(self._down_hist), pen=down_pen, name="Download")
        self.up_curve = self.plot(self._x, list(self._up_hist), pen=up_pen, name="Upload")

        down_brush = QColor(DOWNLOAD_COLOR)
        down_brush.setAlpha(40)
        self.down_curve.setFillLevel(0)
        self.down_curve.setBrush(pg.mkBrush(down_brush))

    def push_sample(self, download_rate: float, upload_rate: float) -> None:
        self._down_hist.append(download_rate)
        self._up_hist.append(upload_rate)
        self.down_curve.setData(self._x, list(self._down_hist))
        self.up_curve.setData(self._x, list(self._up_hist))
