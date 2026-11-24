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
    QMessageBox, QMenu, QAbstractItemView, QHeaderView, QStatusBar, QToolButton,
    QLineEdit, QSizePolicy
)
from PyQt6.QtGui import QAction, QClipboard, QDesktopServices
from PyQt6.QtCore import Qt, QTimer, QPoint, QUrl, QSize

from engine import TorrentEngine, load_config, save_config, TorrentSnapshot
from models import TorrentTableModel, COL_SAVE_PATH
from ui.delegates import TorrentRowDelegate
from ui.add_dialogs import AddTorrentFileDialog, AddMagnetDialog
from ui.settings_dialog import SettingsDialog
from ui.speed_graph import SpeedGraph
from ui.proxy_model import TorrentFilterProxy
from ui.icons import (
    svg_icon, GITHUB_SVG, TELEGRAM_SVG, ADD_FILE_SVG, MAGNET_SVG, PAUSE_SVG,
    RESUME_SVG, REMOVE_SVG, FOLDER_SVG, SETTINGS_SVG, SEARCH_SVG,
)
from ui.theme import TEXT_SECONDARY, TEXT_PRIMARY, TELEGRAM_BLUE
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
        self.proxy_model = TorrentFilterProxy(self)
        self.proxy_model.setSourceModel(self.table_model)
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
            item = QListWidgetItem(f"{name}  ·  0", self.filter_list)
            item.setData(Qt.ItemDataRole.UserRole, name)
        self.filter_list.setCurrentRow(0)
        side_layout.addWidget(self.filter_list, 1)

        # --- main area: table + graph ---
        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.setItemDelegate(TorrentRowDelegate(self.table))
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
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSortIndicatorShown(True)

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

        # --- dev credit links (real GitHub octocat / Telegram paper-plane marks) ---
        self.github_btn = QToolButton()
        self.github_btn.setIcon(svg_icon(GITHUB_SVG, TEXT_PRIMARY))
        self.github_btn.setIconSize(QSize(17, 17))
        self.github_btn.setToolTip("Dev on GitHub: NengzXGODZ")
        self.github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DEV_GITHUB_URL)))

        self.telegram_btn = QToolButton()
        self.telegram_btn.setIcon(svg_icon(TELEGRAM_SVG, TELEGRAM_BLUE))
        self.telegram_btn.setIconSize(QSize(17, 17))
        self.telegram_btn.setToolTip("Dev on Telegram: @nengzx_fernandez")
        self.telegram_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.telegram_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DEV_TELEGRAM_URL)))

        self.status_bar.addPermanentWidget(self.github_btn)
        self.status_bar.addPermanentWidget(self.telegram_btn)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setObjectName("toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        icon_color = TEXT_PRIMARY
        self.act_add_file = QAction(svg_icon(ADD_FILE_SVG, icon_color), "Add Torrent File", self)
        self.act_add_magnet = QAction(svg_icon(MAGNET_SVG, icon_color), "Paste Magnet Link", self)
        self.act_pause = QAction(svg_icon(PAUSE_SVG, icon_color), "Pause", self)
        self.act_resume = QAction(svg_icon(RESUME_SVG, icon_color), "Resume", self)
        self.act_remove = QAction(svg_icon(REMOVE_SVG, icon_color), "Remove", self)
        self.act_open_folder = QAction(svg_icon(FOLDER_SVG, icon_color), "Open Folder", self)
        self.act_settings = QAction(svg_icon(SETTINGS_SVG, icon_color), "Settings", self)

        for act in (self.act_add_file, self.act_add_magnet):
            toolbar.addAction(act)
        toolbar.addSeparator()
        for act in (self.act_pause, self.act_resume, self.act_remove, self.act_open_folder):
            toolbar.addAction(act)
        toolbar.addSeparator()
        toolbar.addAction(self.act_settings)

        # Spacer pushes the search box to the far right of the toolbar.
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search torrents...")
        self.search_box.setFixedWidth(220)
        self.search_box.setClearButtonEnabled(True)
        search_icon_action = QAction(svg_icon(SEARCH_SVG, TEXT_SECONDARY), "", self.search_box)
        self.search_box.addAction(search_icon_action, QLineEdit.ActionPosition.LeadingPosition)
        toolbar.addWidget(self.search_box)

    def _wire_up(self) -> None:
        self.act_add_file.triggered.connect(self.on_add_torrent_file)
        self.act_add_magnet.triggered.connect(self.on_add_magnet)
        self.act_pause.triggered.connect(self.on_pause_selected)
        self.act_resume.triggered.connect(self.on_resume_selected)
        self.act_remove.triggered.connect(self.on_remove_selected)
        self.act_open_folder.triggered.connect(self.on_open_folder_selected)
        self.act_settings.triggered.connect(self.on_open_settings)
        self.filter_list.currentRowChanged.connect(self.on_filter_changed)
        self.search_box.textChanged.connect(self.proxy_model.set_search_text)

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
        # Indexes from the view are proxy indexes (sort/filter applied);
        # QSortFilterProxyModel.data() already maps these to the source
        # model automatically, so no manual mapToSource() is needed here.
        hashes = []
        for index in self.table.selectionModel().selectedRows():
            row: TorrentSnapshot = self.proxy_model.data(index, Qt.ItemDataRole.UserRole)
            if row:
                hashes.append(row.info_hash)
        return hashes

    def on_pause_selected(self) -> None:
        hashes = self._selected_hashes()
        if not hashes:
            return
        for h in hashes:
            self.engine.pause(h)
        self._poll()

    def on_resume_selected(self) -> None:
        hashes = self._selected_hashes()
        if not hashes:
            return
        for h in hashes:
            self.engine.resume(h)
        self._poll()

    def on_remove_selected(self) -> None:
        hashes = self._selected_hashes()
        if not hashes:
            QMessageBox.information(self, "No Torrent Selected", "Select a torrent first, then try again.")
            return

        # Three explicit buttons instead of Yes/No/Cancel: that mapping was
        # ambiguous (Cancel aborted the whole remove, which looked like
        # "remove failed" when someone clicked it just meaning "don't touch
        # my files"). Now every button's label says exactly what it does.
        box = QMessageBox(self)
        box.setWindowTitle("Remove Torrent")
        box.setText(f"Remove {len(hashes)} torrent(s) from the list?")
        remove_only_btn = box.addButton("Remove (Keep Files)", QMessageBox.ButtonRole.YesRole)
        remove_delete_btn = box.addButton("Remove and Delete Files", QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(remove_only_btn)
        box.exec()

        clicked = box.clickedButton()
        if clicked is cancel_btn or clicked is None:
            return
        delete_files = clicked is remove_delete_btn

        for h in hashes:
            self.engine.remove(h, delete_files=delete_files)
        self._poll()

    def on_open_folder_selected(self) -> None:
        hashes = self._selected_hashes()
        if not hashes:
            QMessageBox.information(self, "No Torrent Selected", "Select a torrent first, then try again.")
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

    def on_filter_changed(self, row: int) -> None:
        item = self.filter_list.item(row)
        self._active_filter = item.data(Qt.ItemDataRole.UserRole) if item else "All"
        self._poll()

    def _show_context_menu(self, pos: QPoint) -> None:
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        # Right-clicking a row does NOT select it by default in QTableView,
        # so without this, every action below would act on whatever was
        # selected before (often nothing) instead of the row under the cursor.
        if not self.table.selectionModel().isRowSelected(index.row(), index.parent()):
            self.table.selectRow(index.row())

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

    def _filter_counts(self, torrents: list[TorrentSnapshot]) -> dict:
        return {
            "All": len(torrents),
            "Downloading": sum(1 for r in torrents if r.status == "Downloading"),
            "Seeding": sum(1 for r in torrents if r.status == "Seeding"),
            "Completed": sum(1 for r in torrents if r.is_finished),
            "Paused": sum(1 for r in torrents if r.is_paused),
        }

    def _poll(self) -> None:
        snapshot = self.engine.poll()
        visible_rows = [r for r in snapshot.torrents if self._matches_filter(r)]
        self.table_model.set_rows(visible_rows)

        counts = self._filter_counts(snapshot.torrents)
        for i in range(self.filter_list.count()):
            item = self.filter_list.item(i)
            name = item.data(Qt.ItemDataRole.UserRole)
            item.setText(f"{name}  ·  {counts.get(name, 0)}")

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
