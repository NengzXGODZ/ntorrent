"""
Confirmation dialogs shown when adding a .torrent file or a magnet link:
display name/size, and let the user override the output folder for this
specific download before it's handed to the engine.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QDialogButtonBox, QWidget
)
from PyQt6.QtCore import Qt

from models import human_size


class _OutputFolderRow(QWidget):
    """Reusable 'Output Folder' field + Browse... button."""

    def __init__(self, default_dir: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.path_edit = QLineEdit(default_dir)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse)
        layout.addWidget(self.path_edit, 1)
        layout.addWidget(self.browse_btn)

    def _browse(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.path_edit.text())
        if chosen:
            self.path_edit.setText(chosen)

    def path(self) -> str:
        return self.path_edit.text().strip()


class AddTorrentFileDialog(QDialog):
    """Shown after the user picks a .torrent file: confirms name/size and
    lets them choose where it will be saved."""

    def __init__(self, name: str, size_bytes: int, default_dir: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Torrent")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.addRow("Name:", QLabel(name, wordWrap=True))
        form.addRow("Size:", QLabel(human_size(size_bytes)))
        layout.addLayout(form)

        layout.addWidget(QLabel("Output Folder:"))
        self.output_row = _OutputFolderRow(default_dir)
        layout.addWidget(self.output_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Add Torrent")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save_path(self) -> str:
        return self.output_row.path()


class AddMagnetDialog(QDialog):
    """Paste-a-magnet-link dialog. If a URI is passed in already (e.g. from the
    clipboard), the field is pre-filled; the user can still edit it."""

    def __init__(self, default_dir: str, prefilled_uri: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Magnet Link")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Magnet URI:"))
        self.uri_edit = QLineEdit(prefilled_uri)
        self.uri_edit.setPlaceholderText("magnet:?xt=urn:btih:...")
        layout.addWidget(self.uri_edit)

        layout.addWidget(QLabel("Output Folder:"))
        self.output_row = _OutputFolderRow(default_dir)
        layout.addWidget(self.output_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Add Torrent")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primaryButton")
        buttons.accepted.connect(self._try_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #FF5C5C;")
        layout.addWidget(self._error_label)

    def _try_accept(self) -> None:
        uri = self.uri_edit.text().strip()
        if not uri.lower().startswith("magnet:?"):
            self._error_label.setText("That doesn't look like a valid magnet link.")
            return
        self.accept()

    def magnet_uri(self) -> str:
        return self.uri_edit.text().strip()

    def save_path(self) -> str:
        return self.output_row.path()
