from __future__ import annotations

import os
import shutil
import subprocess
import threading
from typing import Optional, List

from PySide6.QtCore import QObject, Signal

from .ffmpeg_resolver import find_ffmpeg


class FFMpegRunner(QObject):
    on_log = Signal(str)
    on_started = Signal()
    on_stopped = Signal(int)
    on_error = Signal(str)
    on_file_started = Signal(str)  # emits current file path when a file starts

    def __init__(self, ffmpeg_path: Optional[str] = None) -> None:
        super().__init__()
        self._ffmpeg_path = ffmpeg_path or find_ffmpeg() or shutil.which("ffmpeg")
        self._process: Optional[subprocess.Popen] = None
        self._stdout_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._runner_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        with self._lock:
            if self._runner_thread and self._runner_thread.is_alive():
                return True
            return self._process is not None and self._process.poll() is None

    def start_stream(self, *, video_path: str, rtmp_url: str) -> None:
        # Backward-compatible single-file start just wraps playlist of size 1
        self.start_playlist(video_files=[video_path], rtmp_url=rtmp_url, loop=False)

    def start_playlist(self, *, video_files: List[str], rtmp_url: str, loop: bool) -> None:
        if not self._ffmpeg_path:
            self.on_error.emit("FFmpeg tidak ditemukan di PATH. Install FFmpeg terlebih dahulu.")
            return
        if self.is_running:
            self.on_error.emit("Proses FFmpeg masih berjalan.")
            return
        valid_files = [p for p in video_files if p and os.path.isfile(p)]
        if not valid_files:
            self.on_error.emit("Playlist kosong atau file tidak ditemukan.")
            return

        self._stop_event.clear()
        self._runner_thread = threading.Thread(
            target=self._run_playlist_worker, args=(valid_files, rtmp_url, loop), name="ffmpeg-playlist"
        )
        self._runner_thread.daemon = True
        self._runner_thread.start()

    def stop_stream(self) -> None:
        self._stop_event.set()
        with self._lock:
            proc = self._process
        if proc is not None:
            try:
                proc.terminate()
            except Exception:
                pass

    # Internal
    def _run_playlist_worker(self, files: List[str], rtmp_url: str, loop: bool) -> None:
        self.on_started.emit()
        exit_code = 0
        try:
            index = 0
            while not self._stop_event.is_set():
                current = files[index]
                self.on_file_started.emit(current)
                exit_code = self._run_single_file(current, rtmp_url)
                if self._stop_event.is_set():
                    break
                # Advance index
                index += 1
                if index >= len(files):
                    if loop:
                        index = 0
                    else:
                        break
        finally:
            self.on_stopped.emit(exit_code)
            with self._lock:
                self._process = None
                self._stdout_thread = None
                self._stderr_thread = None
                self._runner_thread = None

    def _run_single_file(self, file_path: str, rtmp_url: str) -> int:
        cmd: List[str] = [
            self._ffmpeg_path,
            "-hide_banner",
            "-re",
            "-i",
            file_path,
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
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
            with self._lock:
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
            # Start readers for this process
            self._stdout_thread = threading.Thread(target=self._read_stream, args=(self._process.stdout,))
            self._stderr_thread = threading.Thread(target=self._read_stream, args=(self._process.stderr,))
            self._stdout_thread.daemon = True
            self._stderr_thread.daemon = True
            self._stdout_thread.start()
            self._stderr_thread.start()

            exit_code = self._process.wait()
        except Exception as exc:
            self.on_log.emit(f"[runner] Gagal menjalankan FFmpeg: {exc}\n")
            return -1
        finally:
            # Best-effort cleanup
            with self._lock:
                proc = self._process
            if proc is not None:
                try:
                    if proc.stdout:
                        proc.stdout.close()
                    if proc.stderr:
                        proc.stderr.close()
                except Exception:
                    pass
            if self._stdout_thread:
                self._stdout_thread.join(timeout=0.2)
            if self._stderr_thread:
                self._stderr_thread.join(timeout=0.2)
        return exit_code

    def _read_stream(self, stream) -> None:
        if stream is None:
            return
        for line in stream:
            self.on_log.emit(line)
        try:
            stream.close()
        except Exception:
            pass
