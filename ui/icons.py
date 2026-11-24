"""
Inline SVG -> QIcon helper, plus every icon used in the UI: toolbar glyphs,
the search icon, and the two dev-credit marks (GitHub octocat, Telegram
paper plane) shown in the status bar.
"""
from __future__ import annotations

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer


def svg_icon(svg_text: str, color: str, size: int = 18) -> QIcon:
    colored = svg_text.replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(colored.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


# --------------------------------------------------------------- toolbar
# Plain geometric line glyphs (original constructions, not from any icon
# pack) kept in one consistent stroke style for the toolbar/search box.

ADD_FILE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
  <path d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9.5A1.5 1.5 0 0 1 5.5 19V5A1.5 1.5 0 0 1 7 3.5Z"/>
  <path d="M14 3.5V8h4"/>
  <path d="M12 11v6"/>
  <path d="M9 14h6"/>
</svg>
"""

MAGNET_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
  <path d="M6 4v6a6 6 0 0 0 12 0V4"/>
  <path d="M6 4h3.4"/>
  <path d="M14.6 4H18"/>
  <path d="M6 9.4h3.4"/>
  <path d="M14.6 9.4H18"/>
</svg>
"""

PAUSE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none">
  <rect x="6.5" y="5" width="4" height="14" rx="1.2"/>
  <rect x="13.5" y="5" width="4" height="14" rx="1.2"/>
</svg>
"""

RESUME_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none">
  <path d="M7.5 4.8v14.4a.9.9 0 0 0 1.37.77l11.4-7.2a.9.9 0 0 0 0-1.54l-11.4-7.2A.9.9 0 0 0 7.5 4.8Z"/>
</svg>
"""

REMOVE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
  <path d="M4.5 7h15"/>
  <path d="M9.3 7V4.9c0-.5.4-.9.9-.9h3.6c.5 0 .9.4.9.9V7"/>
  <path d="M7 7l.8 12.1c.05.9.8 1.6 1.7 1.6h5c.9 0 1.65-.7 1.7-1.6L17 7"/>
  <path d="M10.3 11v6"/>
  <path d="M13.7 11v6"/>
</svg>
"""

FOLDER_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3.5 7.3c0-.7.6-1.3 1.3-1.3h4l2 2h8.4c.72 0 1.3.58 1.3 1.3v8.1c0 .72-.58 1.3-1.3 1.3H4.8c-.72 0-1.3-.58-1.3-1.3Z"/>
</svg>
"""

SETTINGS_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="3.1"/>
  <path d="M19.4 13.4a7.6 7.6 0 0 0 0-2.8l2.05-1.5-2-3.46-2.38.82a7.6 7.6 0 0 0-2.42-1.4L14.2 2.8H9.8l-.45 2.3a7.6 7.6 0 0 0-2.42 1.4l-2.38-.82-2 3.46L4.6 10.6a7.6 7.6 0 0 0 0 2.8l-2.05 1.5 2 3.46 2.38-.82a7.6 7.6 0 0 0 2.42 1.4l.45 2.3h4.4l.45-2.3a7.6 7.6 0 0 0 2.42-1.4l2.38.82 2-3.46Z"/>
</svg>
"""

SEARCH_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="10.3" cy="10.3" r="6"/>
  <path d="m20 20-5.6-5.6"/>
</svg>
"""

# --------------------------------------------------------------- dev credit
# Real brand marks (GitHub octocat, Telegram paper-plane), solid fill, used
# purely as "open my profile" links in the status bar -- the same way
# shields.io's logo=github/logo=telegram badges in the README work.

GITHUB_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none">
  <path d="M12 .5C5.73.5.75 5.48.75 11.75c0 5.02 3.26 9.28 7.77 10.78.57.1.78-.25.78-.55
           0-.27-.01-1.17-.02-2.12-3.16.69-3.83-1.36-3.83-1.36-.52-1.31-1.26-1.67-1.26-1.67
           -1.03-.7.08-.69.08-.69 1.14.08 1.74 1.17 1.74 1.17 1.01 1.74 2.65 1.24 3.3.95
           .1-.73.4-1.24.72-1.52-2.52-.29-5.17-1.26-5.17-5.6 0-1.24.44-2.25 1.17-3.04
           -.12-.29-.51-1.46.11-3.04 0 0 .96-.31 3.14 1.16a10.9 10.9 0 0 1 2.86-.39
           c.97 0 1.95.13 2.86.39 2.18-1.47 3.14-1.16 3.14-1.16.62 1.58.23 2.75.11 3.04
           .73.79 1.17 1.8 1.17 3.04 0 4.35-2.66 5.31-5.19 5.59.41.35.77 1.04.77 2.1
           0 1.52-.01 2.74-.01 3.11 0 .3.2.66.78.55 4.5-1.5 7.76-5.76 7.76-10.78
           C23.25 5.48 18.27.5 12 .5Z"/>
</svg>
"""

TELEGRAM_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none">
  <path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0Zm5.47 8.16-1.86 8.77
           c-.14.63-.51.78-1.03.49l-2.85-2.1-1.38 1.33c-.15.15-.28.28-.57.28l.2-2.88 5.24-4.74
           c.23-.2-.05-.32-.35-.12l-6.48 4.08-2.79-.87c-.6-.19-.61-.6.13-.89l10.9-4.2
           c.5-.18.94.12.84.95Z"/>
</svg>
"""
