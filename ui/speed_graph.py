"""
Advanced live speed graph: a 60-second rolling download/upload chart with
a human-readable (KB/s, MB/s) Y-axis, a live current/peak stat row above
the chart, and a mouse-hover crosshair that reads out the exact value at
any point in the last 60 seconds.
"""
from __future__ import annotations

from collections import deque

import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from models import human_rate
from ui.theme import (
    BG_PANEL, BG_ELEVATED, BORDER, TEXT_SECONDARY, TEXT_PRIMARY,
    DOWNLOAD_COLOR, UPLOAD_COLOR,
)

WINDOW_SECONDS = 60

pg.setConfigOptions(antialias=True)


class _RateAxisItem(pg.AxisItem):
    """Left axis that prints '512 KB/s' style labels instead of raw bytes."""

    def tickStrings(self, values, scale, spacing):
        return [human_rate(max(0.0, v)) for v in values]


class _StatChip(QLabel):
    """One small 'label: value' readout in the stat row above the graph."""

    def __init__(self, label: str, color: str, parent=None):
        super().__init__(parent)
        self._label = label
        self._color = color
        self.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; padding: 2px 6px;"
        )
        self.set_value("0 B/s")

    def set_value(self, value_text: str) -> None:
        self.setText(
            f'<span style="color:{self._color}; font-weight:600;">●</span> '
            f'{self._label} <span style="color:{TEXT_PRIMARY}; font-weight:600;">{value_text}</span>'
        )


class SpeedGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- stat row: current + peak for both directions ---
        stat_row = QWidget()
        stat_row.setStyleSheet(f"background-color: {BG_ELEVATED}; border-bottom: 1px solid {BORDER};")
        stat_layout = QHBoxLayout(stat_row)
        stat_layout.setContentsMargins(12, 4, 12, 4)
        stat_layout.setSpacing(18)

        self.chip_down_now = _StatChip("Down", DOWNLOAD_COLOR)
        self.chip_up_now = _StatChip("Up", UPLOAD_COLOR)
        self.chip_down_peak = _StatChip("Peak Down", DOWNLOAD_COLOR)
        self.chip_up_peak = _StatChip("Peak Up", UPLOAD_COLOR)

        for chip in (self.chip_down_now, self.chip_up_now, self.chip_down_peak, self.chip_up_peak):
            stat_layout.addWidget(chip)
        stat_layout.addStretch(1)

        self.hover_label = QLabel("")
        self.hover_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; padding: 2px 6px;")
        stat_layout.addWidget(self.hover_label)

        layout.addWidget(stat_row)

        # --- the plot itself ---
        self.plot = pg.PlotWidget(axisItems={"left": _RateAxisItem(orientation="left")})
        self.plot.setBackground(BG_PANEL)
        self.plot.showGrid(x=True, y=True, alpha=0.12)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()
        self.plot.setMinimumHeight(160)

        axis_pen = pg.mkPen(color=BORDER, width=1)
        for axis_name in ("bottom", "left"):
            axis = self.plot.getAxis(axis_name)
            axis.setPen(axis_pen)
            axis.setTextPen(pg.mkPen(color=TEXT_SECONDARY))

        self.plot.setLabel("bottom", "Seconds ago")
        self.plot.getPlotItem().invertX(True)
        self.plot.addLegend(offset=(10, 6), labelTextColor=TEXT_SECONDARY)
        self.plot.setYRange(0, 1024, padding=0.1)

        # x[i] is the "seconds ago" value for the sample stored at list
        # position i in the (oldest-first) history deques below: position 0
        # is the oldest sample in the window (59s ago), the last position is
        # the newest (0s ago) -- so x must count DOWN, not up, for the
        # "Seconds ago" axis label to actually match which point is where.
        self._x = list(range(WINDOW_SECONDS - 1, -1, -1))
        self._down_hist = deque([0.0] * WINDOW_SECONDS, maxlen=WINDOW_SECONDS)
        self._up_hist = deque([0.0] * WINDOW_SECONDS, maxlen=WINDOW_SECONDS)
        self._peak_down = 0.0
        self._peak_up = 0.0

        down_pen = pg.mkPen(color=DOWNLOAD_COLOR, width=2.2)
        up_pen = pg.mkPen(color=UPLOAD_COLOR, width=2.2)

        self.down_curve = self.plot.plot(self._x, list(self._down_hist), pen=down_pen, name="Download")
        self.up_curve = self.plot.plot(self._x, list(self._up_hist), pen=up_pen, name="Upload")

        down_brush = QColor(DOWNLOAD_COLOR)
        down_brush.setAlpha(36)
        self.down_curve.setFillLevel(0)
        self.down_curve.setBrush(pg.mkBrush(down_brush))

        up_brush = QColor(UPLOAD_COLOR)
        up_brush.setAlpha(22)
        self.up_curve.setFillLevel(0)
        self.up_curve.setBrush(pg.mkBrush(up_brush))

        # --- hover crosshair ---
        crosshair_pen = pg.mkPen(color=TEXT_SECONDARY, width=1, style=Qt.PenStyle.DashLine)
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=crosshair_pen)
        self.v_line.setZValue(10)
        self.v_line.hide()
        self.plot.addItem(self.v_line, ignoreBounds=True)

        self._mouse_proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved, rateLimit=30, slot=self._on_mouse_moved
        )
        self.plot.setMouseTracking(True)

        layout.addWidget(self.plot, 1)

    # ------------------------------------------------------------- update
    def push_sample(self, download_rate: float, upload_rate: float) -> None:
        self._down_hist.append(download_rate)
        self._up_hist.append(upload_rate)
        self._peak_down = max(self._peak_down, download_rate)
        self._peak_up = max(self._peak_up, upload_rate)

        self.down_curve.setData(self._x, list(self._down_hist))
        self.up_curve.setData(self._x, list(self._up_hist))

        visible_max = max(max(self._down_hist, default=0.0), max(self._up_hist, default=0.0))
        self.plot.setYRange(0, max(visible_max * 1.25, 1024), padding=0)

        self.chip_down_now.set_value(human_rate(download_rate))
        self.chip_up_now.set_value(human_rate(upload_rate))
        self.chip_down_peak.set_value(human_rate(self._peak_down))
        self.chip_up_peak.set_value(human_rate(self._peak_up))

    # ------------------------------------------------------------- hover
    def _on_mouse_moved(self, evt) -> None:
        pos = evt[0]
        plot_item = self.plot.getPlotItem()
        if not plot_item.sceneBoundingRect().contains(pos):
            self.v_line.hide()
            self.hover_label.setText("")
            return

        mouse_point = plot_item.vb.mapSceneToView(pos)
        seconds_ago = round(mouse_point.x())
        if seconds_ago < 0 or seconds_ago >= WINDOW_SECONDS:
            self.v_line.hide()
            self.hover_label.setText("")
            return

        self.v_line.setPos(seconds_ago)
        self.v_line.show()

        # self._x[i] == "seconds ago" for the sample at list position i, so
        # recovering the list position from the hovered seconds-ago value is
        # just the mirrored offset.
        idx = WINDOW_SECONDS - 1 - seconds_ago
        if 0 <= idx < len(self._down_hist):
            down_v = list(self._down_hist)[idx]
            up_v = list(self._up_hist)[idx]
            self.hover_label.setText(
                f"{seconds_ago}s ago — ↓ {human_rate(down_v)}  ↑ {human_rate(up_v)}"
            )
