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


def _ffprobe_filename() -> str:
    return "ffprobe.exe" if _platform_dir_name() == "windows" else "ffprobe"


def _candidate_vendor_paths() -> list[Path]:
    fname = _ffprobe_filename()
    platdir = _platform_dir_name()
    candidates: list[Path] = []

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        base = Path(meipass)
        candidates.append(base / "vendor" / platdir / fname)
        candidates.append(base / "rtmp_client" / "vendor" / platdir / fname)

    here = Path(__file__).resolve().parent
    candidates.append(here.parent / "vendor" / platdir / fname)
    app_root = here.parent.parent
    candidates.append(app_root / "vendor" / platdir / fname)

    seen = set()
    unique: list[Path] = []
    for p in candidates:
        if p not in seen:
            unique.append(p)
            seen.add(p)
    return unique


def find_ffprobe() -> Optional[str]:
    for path in _candidate_vendor_paths():
        if path.exists() and os.access(path, os.X_OK):
            return str(path)
    return shutil.which("ffprobe")
