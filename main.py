"""
NTorrent entry point.

Run:  python main.py
"""
import sys

from PyQt6.QtWidgets import QApplication

from ui.theme import STYLESHEET
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("NTorrent")
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    # Support "open with NTorrent" from Explorer / the .torrent file association
    # the installer can register: argv[1] is the double-clicked .torrent path.
    if len(sys.argv) > 1 and sys.argv[1].lower().endswith(".torrent"):
        window.open_torrent_path(sys.argv[1])

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
