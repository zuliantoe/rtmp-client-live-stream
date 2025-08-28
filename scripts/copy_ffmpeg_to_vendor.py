#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import stat
import sys
from pathlib import Path
import platform


def platform_dir() -> str:
    sysname = platform.system().lower()
    if sysname.startswith("darwin") or sysname == "mac" or sysname == "macos":
        return "darwin"
    if sysname.startswith("windows"):
        return "windows"
    return "linux"


def main() -> int:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        print("ffmpeg tidak ditemukan di PATH.")
        return 1
    src = Path(ffmpeg_path)
    dst = Path(__file__).resolve().parents[1] / "rtmp_client" / "vendor" / platform_dir()
    dst.mkdir(parents=True, exist_ok=True)
    target = dst / ("ffmpeg.exe" if platform_dir() == "windows" else "ffmpeg")
    shutil.copy2(src, target)
    # ensure executable
    try:
        mode = os.stat(target).st_mode
        os.chmod(target, mode | stat.S_IEXEC)
    except Exception:
        pass
    print(f"Copied ffmpeg to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
