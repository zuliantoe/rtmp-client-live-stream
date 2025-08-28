from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QLabel,
    QMessageBox,
    QSizePolicy,
)

from rtmp_client.core.ffmpeg_runner import FFMpegRunner
from rtmp_client.core.validators import is_valid_rtmp_url, is_file_readable


class MainWindow(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("RTMP Client")
        self._runner = FFMpegRunner()

        central = QWidget(self)
        self.setCentralWidget(central)

        # Widgets
        self.video_path_edit = QLineEdit(self)
        self.video_path_edit.setPlaceholderText("Pilih file video (MP4/MKV/MOV)")
        self.video_path_edit.setClearButtonEnabled(True)

        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.on_browse_clicked)

        self.rtmp_url_edit = QLineEdit(self)
        self.rtmp_url_edit.setPlaceholderText("rtmp://... atau rtmps://...")
        self.rtmp_url_edit.setClearButtonEnabled(True)

        self.start_button = QPushButton("Start Streaming", self)
        self.start_button.clicked.connect(self.on_start_clicked)

        self.stop_button = QPushButton("Stop Streaming", self)
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.stop_button.setEnabled(False)

        self.status_label = QLabel("Idle", self)
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.log_output = QPlainTextEdit(self)
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QPlainTextEdit.NoWrap)

        # Layouts
        form = QFormLayout()
        file_row = QHBoxLayout()
        file_row.addWidget(self.video_path_edit, 1)
        file_row.addWidget(self.browse_button)
        form.addRow("Video File:", file_row)
        form.addRow("RTMP URL:", self.rtmp_url_edit)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self.start_button)
        buttons_row.addWidget(self.stop_button)

        root_layout = QVBoxLayout(central)
        root_layout.addLayout(form)
        root_layout.addLayout(buttons_row)
        root_layout.addWidget(self.status_label)
        root_layout.addWidget(self.log_output, 1)

        # Wire runner signals
        self._runner.on_log.connect(self.append_log)
        self._runner.on_started.connect(self.on_started)
        self._runner.on_stopped.connect(self.on_stopped)
        self._runner.on_error.connect(self.on_error)

    # Slots
    @Slot()
    def on_browse_clicked(self) -> None:
        start_dir = os.path.expanduser("~")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih File Video",
            start_dir,
            "Video Files (*.mp4 *.mkv *.mov);;All Files (*)",
        )
        if file_path:
            self.video_path_edit.setText(file_path)

    @Slot()
    def on_start_clicked(self) -> None:
        video_path = self.video_path_edit.text().strip()
        rtmp_url = self.rtmp_url_edit.text().strip()

        if not is_file_readable(video_path):
            QMessageBox.warning(self, "Validasi Gagal", "File video tidak valid / tidak bisa dibaca.")
            return
        if not is_valid_rtmp_url(rtmp_url):
            QMessageBox.warning(self, "Validasi Gagal", "RTMP URL harus diawali rtmp:// atau rtmps://")
            return

        self.set_running_ui(True)
        self.append_log("[app] Starting FFmpeg...\n")
        self._runner.start_stream(video_path=video_path, rtmp_url=rtmp_url)

    @Slot()
    def on_stop_clicked(self) -> None:
        self.append_log("[app] Stopping FFmpeg...\n")
        self._runner.stop_stream()

    @Slot()
    def on_started(self) -> None:
        self.status_label.setText("Streaming berjalan...")

    @Slot(int)
    def on_stopped(self, exit_code: int) -> None:
        self.append_log(f"[app] FFmpeg exited with code {exit_code}\n")
        self.status_label.setText("Idle")
        self.set_running_ui(False)

    @Slot(str)
    def on_error(self, message: str) -> None:
        self.append_log(f"[error] {message}\n")
        QMessageBox.critical(self, "Error", message)
        self.set_running_ui(False)

    @Slot(str)
    def append_log(self, text: str) -> None:
        self.log_output.moveCursor(QTextCursor.End)
        self.log_output.insertPlainText(text)
        self.log_output.moveCursor(QTextCursor.End)

    def set_running_ui(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.video_path_edit.setEnabled(not running)
        self.browse_button.setEnabled(not running)
        self.rtmp_url_edit.setEnabled(not running)
