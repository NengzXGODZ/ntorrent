"""
Inline SVG -> QIcon helper, plus the two dev-credit icons (GitHub, Telegram)
shown in the status bar.
"""
from __future__ import annotations

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

# Minimal line-glyph marks (not the official brand artwork) used purely to
# signal "this links to GitHub" / "this links to Telegram" in the footer.
GITHUB_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34
           -.45-1.16-1.11-1.47-1.11-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03
           .9 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.56-1.11-4.56-4.95
           0-1.1.39-1.99 1.03-2.69-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.03a9.5 9.5 0 0 1 5 0
           c1.91-1.3 2.75-1.03 2.75-1.03.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.69
           0 3.85-2.34 4.7-4.57 4.95.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/>
</svg>
"""

TELEGRAM_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <path d="m7.2 12.3 3.4 2.5 1.2-1.3 2.9 3.7c.4.5 1.1.3 1.3-.3l2.4-9.6c.2-.7-.5-1.3-1.2-1.1
           L5.9 10.2c-.7.3-.6 1.2.1 1.4l2.3.7"/>
  <path d="m10.6 14.8-.3 2.9c0 .3.4.5.6.2l1.5-1.7"/>
</svg>
"""


def svg_icon(svg_text: str, color: str, size: int = 18) -> QIcon:
    colored = svg_text.replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(colored.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)
