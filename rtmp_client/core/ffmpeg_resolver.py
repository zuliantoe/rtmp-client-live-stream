from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Optional


def _platform_dir_name() -> str:
    sysname = platform.system().lower()
    if sysname.startswith("darwin") or sysname == "mac" or sysname == "macos":
        return "darwin"
    if sysname.startswith("windows"):
        return "windows"
    return "linux"


def _ffmpeg_filename() -> str:
    return "ffmpeg.exe" if _platform_dir_name() == "windows" else "ffmpeg"


def _candidate_vendor_paths() -> list[Path]:
    fname = _ffmpeg_filename()
    platdir = _platform_dir_name()
    candidates: list[Path] = []

    # PyInstaller temp folder
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        base = Path(meipass)
        candidates.append(base / "vendor" / platdir / fname)
        candidates.append(base / "rtmp_client" / "vendor" / platdir / fname)

    # Package-relative paths (development)
    here = Path(__file__).resolve().parent
    candidates.append(here.parent / "vendor" / platdir / fname)

    # App root vendor dir (if running from project root)
    app_root = here.parent.parent
    candidates.append(app_root / "vendor" / platdir / fname)

    # Unique, preserve order
    seen = set()
    unique: list[Path] = []
    for p in candidates:
        if p not in seen:
            unique.append(p)
            seen.add(p)
    return unique


def find_ffmpeg() -> Optional[str]:
    for path in _candidate_vendor_paths():
        if path.exists() and os.access(path, os.X_OK):
            return str(path)
    # Fallback to PATH
    which = shutil.which("ffmpeg")
    return which
