"""
NTorrent entry point.

Run:  python main.py
"""
import os
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from ui.theme import STYLESHEET
from ui.main_window import MainWindow


def resource_path(relative_path: str) -> str:
    """Resolve a bundled asset both when run from source and when frozen by
    PyInstaller, which unpacks data files into a temp dir at sys._MEIPASS."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("NTorrent")
    app.setStyleSheet(STYLESHEET)

    icon_path = resource_path(os.path.join("assets", "n.png"))
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    else:
        app_icon = QIcon()

    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()

    # Support "open with NTorrent" from Explorer / the .torrent file association
    # the installer can register: argv[1] is the double-clicked .torrent path.
    if len(sys.argv) > 1 and sys.argv[1].lower().endswith(".torrent"):
        window.open_torrent_path(sys.argv[1])

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
