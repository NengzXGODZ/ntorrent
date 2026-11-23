"""
Dark theme palette and global QSS stylesheet for NTorrent.
"""

# Palette constants, reused by widgets that need raw colors (e.g. the speed graph).
BG_WINDOW = "#121212"
BG_PANEL = "#1E1E1E"
BG_ELEVATED = "#242424"
BG_HOVER = "#2A2A2A"
BORDER = "#303030"
TEXT_PRIMARY = "#E8E8E8"
TEXT_SECONDARY = "#9A9A9A"
ACCENT_CYAN = "#00E5C9"
ACCENT_EMERALD = "#2ECC71"
ACCENT_BLUE = "#3DA9FC"
ACCENT_ORANGE = "#FF9F43"
ACCENT_RED = "#FF5C5C"
ACCENT_YELLOW = "#F5D547"

DOWNLOAD_COLOR = ACCENT_CYAN
UPLOAD_COLOR = ACCENT_ORANGE

STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
    color: {TEXT_PRIMARY};
    outline: none;
}}

QMainWindow, QDialog {{
    background-color: {BG_WINDOW};
}}

QWidget#sidebar {{
    background-color: {BG_PANEL};
    border-right: 1px solid {BORDER};
}}

QWidget#toolbar {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
}}

QWidget#statusbar {{
    background-color: {BG_PANEL};
    border-top: 1px solid {BORDER};
}}

QLabel#sectionTitle {{
    color: {TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    padding: 10px 14px 4px 14px;
}}

QListWidget#filterList {{
    background-color: transparent;
    border: none;
    padding: 4px;
}}

QListWidget#filterList::item {{
    padding: 8px 12px;
    border-radius: 6px;
    margin: 1px 4px;
    color: {TEXT_SECONDARY};
}}

QListWidget#filterList::item:selected {{
    background-color: {BG_ELEVATED};
    color: {ACCENT_CYAN};
    font-weight: 600;
}}

QListWidget#filterList::item:hover:!selected {{
    background-color: {BG_HOVER};
}}

QTableView {{
    background-color: {BG_WINDOW};
    alternate-background-color: {BG_PANEL};
    gridline-color: {BORDER};
    border: none;
    selection-background-color: #1B3B38;
    selection-color: {TEXT_PRIMARY};
}}

QTableView::item {{
    padding: 6px 4px;
    border-bottom: 1px solid {BORDER};
}}

QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    padding: 8px 6px;
    border: none;
    border-bottom: 1px solid {BORDER};
    border-right: 1px solid {BORDER};
    font-weight: 600;
}}

QProgressBar {{
    background-color: {BG_ELEVATED};
    border: none;
    border-radius: 4px;
    height: 14px;
    text-align: center;
    color: {TEXT_PRIMARY};
    font-size: 11px;
}}

QProgressBar::chunk {{
    background-color: {ACCENT_CYAN};
    border-radius: 4px;
}}

QPushButton {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 14px;
    color: {TEXT_PRIMARY};
}}

QPushButton:hover {{
    background-color: {BG_HOVER};
    border-color: {ACCENT_CYAN};
}}

QPushButton:pressed {{
    background-color: #1A1A1A;
}}

QPushButton:disabled {{
    color: {TEXT_SECONDARY};
    border-color: {BORDER};
}}

QPushButton#primaryButton {{
    background-color: {ACCENT_CYAN};
    color: #0A0A0A;
    font-weight: 600;
    border: none;
}}

QPushButton#primaryButton:hover {{
    background-color: #1FF0D4;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    color: {TEXT_PRIMARY};
}}

QToolButton:hover {{
    background-color: {BG_HOVER};
}}

QToolButton:pressed {{
    background-color: {BG_ELEVATED};
}}

QLineEdit, QSpinBox, QComboBox, QPlainTextEdit {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_CYAN};
    selection-color: #0A0A0A;
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {ACCENT_CYAN};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    selection-background-color: {BG_HOVER};
}}

QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {BORDER};
    background-color: {BG_ELEVATED};
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_CYAN};
    border-color: {ACCENT_CYAN};
}}

QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: {BG_PANEL};
    padding: 8px 16px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    color: {TEXT_SECONDARY};
}}

QTabBar::tab:selected {{
    background-color: {BG_ELEVATED};
    color: {ACCENT_CYAN};
}}

QScrollBar:vertical {{
    background: {BG_WINDOW};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BG_ELEVATED};
    border-radius: 5px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {BORDER};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {BG_WINDOW};
    height: 10px;
}}

QScrollBar::handle:horizontal {{
    background: {BG_ELEVATED};
    border-radius: 5px;
    min-width: 24px;
}}

QLabel#statusLabel {{
    color: {TEXT_SECONDARY};
    padding: 2px 10px;
}}

QMenu {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 20px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {BG_HOVER};
    color: {ACCENT_CYAN};
}}

QSplitter::handle {{
    background-color: {BORDER};
}}
"""
