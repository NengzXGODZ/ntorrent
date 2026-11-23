"""
NTorrent main window: toolbar, status sidebar, torrent table, speed graph,
and status bar. Polls the engine on a QTimer so all libtorrent calls happen
on the UI thread without ever blocking it (polling libtorrent's status
objects is cheap; it does not touch the network itself).
"""
from __future__ import annotations

import os
import sys

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QToolBar,
    QTableView, QListWidget, QListWidgetItem, QLabel, QFileDialog,
    QMessageBox, QMenu, QAbstractItemView, QHeaderView, QStatusBar, QToolButton
)
from PyQt6.QtGui import QAction, QClipboard, QDesktopServices
from PyQt6.QtCore import Qt, QTimer, QPoint, QUrl, QSize

from engine import TorrentEngine, load_config, save_config, TorrentSnapshot
from models import TorrentTableModel, COL_SAVE_PATH
from ui.delegates import ProgressBarDelegate
from ui.add_dialogs import AddTorrentFileDialog, AddMagnetDialog
from ui.settings_dialog import SettingsDialog
from ui.speed_graph import SpeedGraph
from ui.icons import svg_icon, GITHUB_SVG, TELEGRAM_SVG
from ui.theme import TEXT_SECONDARY
from models import human_rate, human_size

DEV_GITHUB_URL = "https://github.com/NengzXGODZ"
DEV_TELEGRAM_URL = "https://t.me/nengzx_fernandez"

POLL_INTERVAL_MS = 1000
RESUME_SAVE_INTERVAL_MS = 60_000

FILTERS = ["All", "Downloading", "Seeding", "Completed", "Paused"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NTorrent")
        self.resize(1200, 760)

        self.config = load_config()
        self.engine = TorrentEngine(self.config)
        self.table_model = TorrentTableModel(self)
        self._active_filter = "All"

        self._build_ui()
        self._build_toolbar()
        self._wire_up()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._poll)
        self.poll_timer.start(POLL_INTERVAL_MS)

        self.resume_timer = QTimer(self)
        self.resume_timer.timeout.connect(self.engine.save_all_resume_data)
        self.resume_timer.start(RESUME_SAVE_INTERVAL_MS)

        self._poll()  # immediate first paint

    # ------------------------------------------------------------- build
    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- sidebar ---
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(190)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)

        title = QLabel("STATUS")
        title.setObjectName("sectionTitle")
        side_layout.addWidget(title)

        self.filter_list = QListWidget()
        self.filter_list.setObjectName("filterList")
        self.filter_list.setFrameShape(QListWidget.Shape.NoFrame)
        for name in FILTERS:
            QListWidgetItem(name, self.filter_list)
        self.filter_list.setCurrentRow(0)
        side_layout.addWidget(self.filter_list, 1)

        # --- main area: table + graph ---
        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.table = QTableView()
        self.table.setModel(self.table_model)
        self.table.setItemDelegate(ProgressBarDelegate(self.table))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.graph = SpeedGraph()

        main_layout.addWidget(self.table, 1)
        main_layout.addWidget(self.graph, 0)

        splitter.addWidget(sidebar)
        splitter.addWidget(main_area)
        splitter.setStretchFactor(1, 1)
        splitter.setCollapsible(0, False)

        root.addWidget(splitter)
        self.setCentralWidget(central)

        # --- status bar ---
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("statusbar")
        self.setStatusBar(self.status_bar)

        self.dht_label = QLabel("DHT: 0 nodes")
        self.dht_label.setObjectName("statusLabel")
        self.session_totals_label = QLabel("↓ 0 B  ↑ 0 B")
        self.session_totals_label.setObjectName("statusLabel")
        self.connection_label = QLabel("● Listening")
        self.connection_label.setObjectName("statusLabel")

        self.status_bar.addWidget(self.connection_label)
        self.status_bar.addPermanentWidget(self.dht_label)
        self.status_bar.addPermanentWidget(self.session_totals_label)

        # --- dev credit links (GitHub / Telegram) ---
        self.github_btn = QToolButton()
        self.github_btn.setIcon(svg_icon(GITHUB_SVG, TEXT_SECONDARY))
        self.github_btn.setIconSize(QSize(16, 16))
        self.github_btn.setToolTip("Dev on GitHub: NengzXGODZ")
        self.github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DEV_GITHUB_URL)))

        self.telegram_btn = QToolButton()
        self.telegram_btn.setIcon(svg_icon(TELEGRAM_SVG, TEXT_SECONDARY))
        self.telegram_btn.setIconSize(QSize(16, 16))
        self.telegram_btn.setToolTip("Dev on Telegram: @nengzx_fernandez")
        self.telegram_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.telegram_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DEV_TELEGRAM_URL)))

        self.status_bar.addPermanentWidget(self.github_btn)
        self.status_bar.addPermanentWidget(self.telegram_btn)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setObjectName("toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(toolbar.iconSize())
        self.addToolBar(toolbar)

        self.act_add_file = QAction("Add Torrent File", self)
        self.act_add_magnet = QAction("Paste Magnet Link", self)
        self.act_pause = QAction("Pause", self)
        self.act_resume = QAction("Resume", self)
        self.act_remove = QAction("Remove", self)
        self.act_open_folder = QAction("Open Folder", self)
        self.act_settings = QAction("Settings", self)

        for act in (self.act_add_file, self.act_add_magnet):
            toolbar.addAction(act)
        toolbar.addSeparator()
        for act in (self.act_pause, self.act_resume, self.act_remove, self.act_open_folder):
            toolbar.addAction(act)
        toolbar.addSeparator()
        toolbar.addAction(self.act_settings)

    def _wire_up(self) -> None:
        self.act_add_file.triggered.connect(self.on_add_torrent_file)
        self.act_add_magnet.triggered.connect(self.on_add_magnet)
        self.act_pause.triggered.connect(self.on_pause_selected)
        self.act_resume.triggered.connect(self.on_resume_selected)
        self.act_remove.triggered.connect(self.on_remove_selected)
        self.act_open_folder.triggered.connect(self.on_open_folder_selected)
        self.act_settings.triggered.connect(self.on_open_settings)
        self.filter_list.currentTextChanged.connect(self.on_filter_changed)

    # --------------------------------------------------------------- add
    def on_add_torrent_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Torrent File", "", "Torrent Files (*.torrent)")
        if not file_path:
            return
        self.open_torrent_path(file_path)

    def open_torrent_path(self, file_path: str) -> None:
        """Shared by the toolbar file picker and the .torrent file association
        (double-click in Explorer -> NTorrent launched with argv[1] = path)."""
        try:
            name, size = self.engine.peek_torrent_file_info(file_path)
        except Exception as exc:
            QMessageBox.critical(self, "Invalid Torrent", f"Could not read torrent file:\n{exc}")
            return

        dlg = AddTorrentFileDialog(name, size, self.config["download_dir"], self)
        if dlg.exec():
            save_path = dlg.save_path()
            os.makedirs(save_path, exist_ok=True)
            try:
                self.engine.add_torrent_file(file_path, save_path)
            except Exception as exc:
                QMessageBox.critical(self, "Failed to Add Torrent", str(exc))
                return
            self._poll()

    def on_add_magnet(self) -> None:
        clipboard_text = ""
        cb_text = self._clipboard_text()
        if cb_text.lower().startswith("magnet:?"):
            clipboard_text = cb_text

        dlg = AddMagnetDialog(self.config["download_dir"], clipboard_text, self)
        if dlg.exec():
            save_path = dlg.save_path()
            os.makedirs(save_path, exist_ok=True)
            try:
                self.engine.add_magnet(dlg.magnet_uri(), save_path)
            except Exception as exc:
                QMessageBox.critical(self, "Failed to Add Magnet", str(exc))
                return
            self._poll()

    def _clipboard_text(self) -> str:
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        return clipboard.text().strip() if clipboard else ""

    # ----------------------------------------------------------- actions
    def _selected_hashes(self) -> list[str]:
        hashes = []
        for index in self.table.selectionModel().selectedRows():
            row: TorrentSnapshot = self.table_model.data(index, Qt.ItemDataRole.UserRole)
            if row:
                hashes.append(row.info_hash)
        return hashes

    def on_pause_selected(self) -> None:
        for h in self._selected_hashes():
            self.engine.pause(h)
        self._poll()

    def on_resume_selected(self) -> None:
        for h in self._selected_hashes():
            self.engine.resume(h)
        self._poll()

    def on_remove_selected(self) -> None:
        hashes = self._selected_hashes()
        if not hashes:
            return
        resp = QMessageBox.question(
            self, "Remove Torrent",
            f"Remove {len(hashes)} torrent(s) from the list?\n\n"
            "Click 'Yes' to also delete the downloaded files from disk.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if resp == QMessageBox.StandardButton.Cancel:
            return
        delete_files = resp == QMessageBox.StandardButton.Yes
        for h in hashes:
            self.engine.remove(h, delete_files=delete_files)
        self._poll()

    def on_open_folder_selected(self) -> None:
        hashes = self._selected_hashes()
        if not hashes:
            return
        path = self.engine.get_save_path(hashes[0])
        if path and os.path.isdir(path):
            if sys.platform == "win32":
                os.startfile(path)  # noqa: S606 - intentional, opens Explorer at the save path
            else:
                QMessageBox.information(self, "Open Folder", f"Save path:\n{path}")
        else:
            QMessageBox.warning(self, "Folder Not Found", "The save path for this torrent no longer exists.")

    def on_open_settings(self) -> None:
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            new_config = dlg.result_config()
            self.config = new_config
            self.engine.apply_settings(new_config)
            save_config(new_config)

    def on_filter_changed(self, text: str) -> None:
        self._active_filter = text or "All"
        self._poll()

    def _show_context_menu(self, pos: QPoint) -> None:
        if not self.table.indexAt(pos).isValid():
            return
        menu = QMenu(self)
        menu.addAction("Open Output Folder", self.on_open_folder_selected)
        menu.addSeparator()
        menu.addAction("Pause", self.on_pause_selected)
        menu.addAction("Resume", self.on_resume_selected)
        menu.addSeparator()
        menu.addAction("Remove", self.on_remove_selected)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    # ------------------------------------------------------------- poll
    def _matches_filter(self, row: TorrentSnapshot) -> bool:
        if self._active_filter == "All":
            return True
        if self._active_filter == "Downloading":
            return row.status == "Downloading"
        if self._active_filter == "Seeding":
            return row.status == "Seeding"
        if self._active_filter == "Completed":
            return row.is_finished
        if self._active_filter == "Paused":
            return row.is_paused
        return True

    def _poll(self) -> None:
        snapshot = self.engine.poll()
        visible_rows = [r for r in snapshot.torrents if self._matches_filter(r)]
        self.table_model.set_rows(visible_rows)

        self.graph.push_sample(snapshot.download_rate, snapshot.upload_rate)

        self.dht_label.setText(f"DHT: {snapshot.dht_nodes} nodes")
        self.session_totals_label.setText(
            f"↓ {human_size(snapshot.total_download)}  ({human_rate(snapshot.download_rate)})   "
            f"↑ {human_size(snapshot.total_upload)}  ({human_rate(snapshot.upload_rate)})"
        )
        self.connection_label.setText(
            f"● Listening — {snapshot.num_peers} peers connected" if snapshot.listening else "○ Not listening"
        )

        self.setWindowTitle(
            f"NTorrent — ↓ {human_rate(snapshot.download_rate)}  ↑ {human_rate(snapshot.upload_rate)}"
        )

    # ------------------------------------------------------------ close
    def closeEvent(self, event) -> None:
        self.poll_timer.stop()
        self.resume_timer.stop()
        self.engine.shutdown()
        super().closeEvent(event)
