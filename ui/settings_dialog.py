"""
Settings dialog: default download folder, speed limits, max connections, port.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QSpinBox, QDialogButtonBox
)


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(440)
        self._config = config

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        # Default download folder
        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit(config["download_dir"])
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(browse_btn)
        form.addRow("Default Download Folder:", folder_row)

        # Download limit
        self.down_limit = QSpinBox()
        self.down_limit.setRange(0, 10_000_000)
        self.down_limit.setSuffix(" KiB/s (0 = unlimited)")
        self.down_limit.setValue(config["download_limit_kibs"])
        form.addRow("Download Speed Limit:", self.down_limit)

        # Upload limit
        self.up_limit = QSpinBox()
        self.up_limit.setRange(0, 10_000_000)
        self.up_limit.setSuffix(" KiB/s (0 = unlimited)")
        self.up_limit.setValue(config["upload_limit_kibs"])
        form.addRow("Upload Speed Limit:", self.up_limit)

        # Max connections
        self.max_conn = QSpinBox()
        self.max_conn.setRange(10, 20000)
        self.max_conn.setValue(config["max_connections"])
        form.addRow("Max Active Connections:", self.max_conn)

        # Listening port
        self.listen_port = QSpinBox()
        self.listen_port.setRange(1024, 65535)
        self.listen_port.setValue(config["listen_port"])
        form.addRow("Listening Port:", self.listen_port)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Select Default Download Folder", self.folder_edit.text())
        if chosen:
            self.folder_edit.setText(chosen)

    def result_config(self) -> dict:
        cfg = dict(self._config)
        cfg["download_dir"] = self.folder_edit.text().strip() or self._config["download_dir"]
        cfg["download_limit_kibs"] = self.down_limit.value()
        cfg["upload_limit_kibs"] = self.up_limit.value()
        cfg["max_connections"] = self.max_conn.value()
        cfg["listen_port"] = self.listen_port.value()
        return cfg
