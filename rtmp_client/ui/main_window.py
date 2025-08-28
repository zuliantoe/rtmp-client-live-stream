from __future__ import annotations

import os
import re
from typing import Optional

from PySide6.QtCore import Qt, Slot, QUrl
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
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QGroupBox,
    QAbstractItemView,
    QSplitter,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from rtmp_client.core.ffmpeg_runner import FFMpegRunner
from rtmp_client.core.validators import is_valid_rtmp_url, is_file_readable


class MainWindow(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("RTMP Client")
        self._runner = FFMpegRunner()

        central = QWidget(self)
        self.setCentralWidget(central)

        # Single-file widgets (kept for convenience)
        self.video_path_edit = QLineEdit(self)
        self.video_path_edit.setPlaceholderText("Pilih file video (MP4/MKV/MOV)")
        self.video_path_edit.setClearButtonEnabled(True)

        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.on_browse_clicked)

        # Playlist widgets
        self.playlist = QListWidget(self)
        self.playlist.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.add_videos_button = QPushButton("Add Video(s)", self)
        self.add_videos_button.clicked.connect(self.on_add_videos)
        self.remove_selected_button = QPushButton("Remove Selected", self)
        self.remove_selected_button.clicked.connect(self.on_remove_selected)
        self.move_up_button = QPushButton("Move Up", self)
        self.move_up_button.clicked.connect(self.on_move_up)
        self.move_down_button = QPushButton("Move Down", self)
        self.move_down_button.clicked.connect(self.on_move_down)
        self.loop_checkbox = QCheckBox("Loop Playlist", self)

        # RTMP URL
        self.rtmp_url_edit = QLineEdit(self)
        self.rtmp_url_edit.setPlaceholderText("rtmp://... atau rtmps://...")
        self.rtmp_url_edit.setClearButtonEnabled(True)

        # Controls
        self.start_button = QPushButton("Start Streaming", self)
        self.start_button.clicked.connect(self.on_start_clicked)
        self.stop_button = QPushButton("Stop Streaming", self)
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.stop_button.setEnabled(False)

        # Status and connection quality
        self.status_label = QLabel("Idle", self)
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.conn_label = QLabel("", self)
        self.conn_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Log output
        self.log_output = QPlainTextEdit(self)
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QPlainTextEdit.NoWrap)

        # Preview setup (QtMultimedia)
        self.preview_group = QGroupBox("Preview", self)
        preview_layout = QVBoxLayout(self.preview_group)
        self.video_widget = QVideoWidget(self.preview_group)
        preview_layout.addWidget(self.video_widget)
        self.media_player = QMediaPlayer(self.preview_group)
        self.audio_output = QAudioOutput(self.preview_group)
        self.audio_output.setVolume(0.0)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Layouts
        form = QFormLayout()
        file_row = QHBoxLayout()
        file_row.addWidget(self.video_path_edit, 1)
        file_row.addWidget(self.browse_button)
        form.addRow("Video File:", file_row)
        form.addRow("RTMP URL:", self.rtmp_url_edit)

        playlist_group = QGroupBox("Playlist", self)
        playlist_layout = QVBoxLayout(playlist_group)
        playlist_layout.addWidget(self.playlist, 1)
        playlist_buttons_row = QHBoxLayout()
        playlist_buttons_row.addWidget(self.add_videos_button)
        playlist_buttons_row.addWidget(self.remove_selected_button)
        playlist_buttons_row.addStretch(1)
        playlist_buttons_row.addWidget(self.move_up_button)
        playlist_buttons_row.addWidget(self.move_down_button)
        playlist_layout.addLayout(playlist_buttons_row)
        playlist_layout.addWidget(self.loop_checkbox)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self.start_button)
        buttons_row.addWidget(self.stop_button)

        # Left side (inputs + playlist)
        left_widget = QWidget(self)
        left_layout = QVBoxLayout(left_widget)
        left_layout.addLayout(form)
        left_layout.addWidget(playlist_group, 1)

        # Right side (preview + status + controls + logs)
        right_widget = QWidget(self)
        right_layout = QVBoxLayout(right_widget)
        self.preview_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setMinimumHeight(240)
        right_layout.addWidget(self.preview_group, 3)
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(self.conn_label)
        right_layout.addLayout(buttons_row)
        right_layout.addWidget(self.log_output, 2)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        root_layout = QVBoxLayout(central)
        root_layout.addWidget(splitter, 1)

        # Wire runner signals
        self._runner.on_log.connect(self.append_log)
        self._runner.on_started.connect(self.on_started)
        self._runner.on_stopped.connect(self.on_stopped)
        self._runner.on_error.connect(self.on_error)
        self._runner.on_file_started.connect(self.on_file_started)

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
    def on_add_videos(self) -> None:
        start_dir = os.path.expanduser("~")
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Pilih Video (bisa multiple)",
            start_dir,
            "Video Files (*.mp4 *.mkv *.mov);;All Files (*)",
        )
        for f in files:
            if f and os.path.isfile(f):
                self.playlist.addItem(f)

    @Slot()
    def on_remove_selected(self) -> None:
        for item in self.playlist.selectedItems():
            row = self.playlist.row(item)
            self.playlist.takeItem(row)

    @Slot()
    def on_move_up(self) -> None:
        rows = sorted([self.playlist.row(i) for i in self.playlist.selectedItems()])
        if not rows:
            return
        for row in rows:
            if row == 0:
                continue
            item = self.playlist.takeItem(row)
            self.playlist.insertItem(row - 1, item)
            item.setSelected(True)

    @Slot()
    def on_move_down(self) -> None:
        rows = sorted([self.playlist.row(i) for i in self.playlist.selectedItems()], reverse=True)
        if not rows:
            return
        for row in rows:
            if row >= self.playlist.count() - 1:
                continue
            item = self.playlist.takeItem(row)
            self.playlist.insertItem(row + 1, item)
            item.setSelected(True)

    @Slot()
    def on_start_clicked(self) -> None:
        # Prefer playlist if available
        files = [self.playlist.item(i).text() for i in range(self.playlist.count())]
        rtmp_url = self.rtmp_url_edit.text().strip()
        loop = self.loop_checkbox.isChecked()

        if files:
            # Validate at least the first file exists
            if not any(os.path.isfile(p) for p in files):
                QMessageBox.warning(self, "Validasi Gagal", "Playlist kosong atau file tidak valid.")
                return
            if not is_valid_rtmp_url(rtmp_url):
                QMessageBox.warning(self, "Validasi Gagal", "RTMP URL harus diawali rtmp:// atau rtmps://")
                return
            self.set_running_ui(True)
            self.append_log("[app] Starting FFmpeg (playlist)...\n")
            self._runner.start_playlist(video_files=files, rtmp_url=rtmp_url, loop=loop)
            return

        # Fallback single file
        video_path = self.video_path_edit.text().strip()
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
        self.media_player.stop()

    @Slot()
    def on_started(self) -> None:
        self.status_label.setText("Streaming berjalan...")

    @Slot(str)
    def on_file_started(self, file_path: str) -> None:
        base = os.path.basename(file_path)
        self.status_label.setText(f"Streaming: {base}")
        # Start preview of the local file, muted
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.play()

    @Slot(int)
    def on_stopped(self, exit_code: int) -> None:
        self.append_log(f"[app] FFmpeg exited with code {exit_code}\n")
        self.status_label.setText("Idle")
        self.conn_label.setText("")
        self.media_player.stop()
        self.set_running_ui(False)

    @Slot(str)
    def on_error(self, message: str) -> None:
        self.append_log(f"[error] {message}\n")
        QMessageBox.critical(self, "Error", message)
        self.media_player.stop()
        self.set_running_ui(False)

    @Slot(str)
    def append_log(self, text: str) -> None:
        self.log_output.moveCursor(QTextCursor.End)
        self.log_output.insertPlainText(text)
        self.log_output.moveCursor(QTextCursor.End)
        self._maybe_update_metrics(text)

    def set_running_ui(self, running: bool) -> None:
        # Disable inputs during running
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.video_path_edit.setEnabled(not running)
        self.browse_button.setEnabled(not running)
        self.rtmp_url_edit.setEnabled(not running)
        self.playlist.setEnabled(not running)
        self.add_videos_button.setEnabled(not running)
        self.remove_selected_button.setEnabled(not running)
        self.move_up_button.setEnabled(not running)
        self.move_down_button.setEnabled(not running)
        self.loop_checkbox.setEnabled(not running)

    # Parse FFmpeg progress line for fps/bitrate/speed
    def _maybe_update_metrics(self, line: str) -> None:
        if "frame=" not in line or "bitrate=" not in line:
            return
        # Example: frame=  110 fps= 25 q=28.0 size=    1024kB time=00:00:04.40 bitrate= 1902.2kbits/s speed=1.01x
        fps_match = re.search(r"fps=\s*([\d.]+)", line)
        br_match = re.search(r"bitrate=\s*([\d.]+)\s*([kM])?bits/s", line)
        sp_match = re.search(r"speed=\s*([\d.]+x)", line)
        if not (fps_match or br_match or sp_match):
            return
        parts = []
        if fps_match:
            parts.append(f"FPS: {fps_match.group(1)}")
        if br_match:
            val = float(br_match.group(1))
            unit = br_match.group(2) or ""
            if unit == "M":
                kbps = int(val * 1000)
            else:
                kbps = int(val)
            parts.append(f"Bitrate: {kbps} kbps")
        if sp_match:
            parts.append(f"Speed: {sp_match.group(1)}")
        if parts:
            self.conn_label.setText(" | ".join(parts))
