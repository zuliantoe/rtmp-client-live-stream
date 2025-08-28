from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from typing import Optional, List

from PySide6.QtCore import QObject, Signal


class FFMpegRunner(QObject):
    on_log = Signal(str)
    on_started = Signal()
    on_stopped = Signal(int)
    on_error = Signal(str)

    def __init__(self, ffmpeg_path: Optional[str] = None) -> None:
        super().__init__()
        self._ffmpeg_path = ffmpeg_path or shutil.which("ffmpeg")
        self._process: Optional[subprocess.Popen] = None
        self._stdout_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def start_stream(self, *, video_path: str, rtmp_url: str) -> None:
        if not self._ffmpeg_path:
            self.on_error.emit("FFmpeg tidak ditemukan di PATH. Install FFmpeg terlebih dahulu.")
            return
        if self.is_running:
            self.on_error.emit("Proses FFmpeg masih berjalan.")
            return
        if not os.path.isfile(video_path):
            self.on_error.emit("File video tidak ditemukan.")
            return

        # Base MVP command
        cmd: List[str] = [
            self._ffmpeg_path,
            "-hide_banner",
            "-re",
            "-i",
            video_path,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            "2500k",
            "-c:a",
            "aac",
            "-ar",
            "44100",
            "-b:a",
            "128k",
            "-f",
            "flv",
            rtmp_url,
        ]

        try:
            creationflags = 0
            startupinfo = None
            # On Windows, hide console window
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=creationflags,
                startupinfo=startupinfo,
            )
        except Exception as exc:
            self._process = None
            self.on_error.emit(f"Gagal menjalankan FFmpeg: {exc}")
            return

        self._stdout_thread = threading.Thread(target=self._read_stream, args=(self._process.stdout,))
        self._stderr_thread = threading.Thread(target=self._read_stream, args=(self._process.stderr,))
        self._stdout_thread.daemon = True
        self._stderr_thread.daemon = True
        self._stdout_thread.start()
        self._stderr_thread.start()

        self.on_started.emit()

        watcher = threading.Thread(target=self._wait_for_exit)
        watcher.daemon = True
        watcher.start()

    def stop_stream(self) -> None:
        with self._lock:
            proc = self._process
        if not proc:
            return

        try:
            proc.terminate()
        except Exception:
            pass

        # Give it a moment to exit gracefully
        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
            try:
                proc.wait(timeout=3)
            except Exception:
                pass

    def _read_stream(self, stream) -> None:
        if stream is None:
            return
        for line in stream:
            self.on_log.emit(line)
        try:
            stream.close()
        except Exception:
            pass

    def _wait_for_exit(self) -> None:
        with self._lock:
            proc = self._process
        if not proc:
            return
        exit_code = proc.wait()
        self.on_stopped.emit(exit_code)
        with self._lock:
            self._process = None
            self._stdout_thread = None
            self._stderr_thread = None
