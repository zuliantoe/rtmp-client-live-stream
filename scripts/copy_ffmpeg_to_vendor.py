#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def ensure_exec(path: Path) -> None:
    try:
        mode = os.stat(path).st_mode
        os.chmod(path, mode | stat.S_IEXEC)
    except Exception:
        pass


def copy_windows_bundle(src_bin: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    # Copy exes
    for exe in ("ffmpeg.exe", "ffprobe.exe"):
        src = src_bin / exe
        if src.exists():
            shutil.copy2(src, dst_dir / exe)
            ensure_exec(dst_dir / exe)
    # Copy DLLs in same bin dir
    for dll in src_bin.glob("*.dll"):
        shutil.copy2(dll, dst_dir / dll.name)


def copy_unix_ffmpeg(src_ffmpeg: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    target = dst_dir / "ffmpeg"
    shutil.copy2(src_ffmpeg, target)
    ensure_exec(target)


def detect_windows_bin_from_ffmpeg(ffmpeg_path: Path) -> Path:
    # If ffmpeg.exe given, bin dir is its parent
    if ffmpeg_path.name.lower() == "ffmpeg.exe":
        return ffmpeg_path.parent
    # If pointed to a bin directory
    if ffmpeg_path.is_dir():
        return ffmpeg_path
    # Otherwise use parent
    return ffmpeg_path.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy ffmpeg (and deps) into vendor folder for bundling")
    parser.add_argument(
        "source",
        nargs="?",
        help="Optional path to ffmpeg bin directory or ffmpeg executable. If omitted, will use ffmpeg from PATH.",
    )
    args = parser.parse_args()

    plat = platform_dir()
    project_root = Path(__file__).resolve().parents[1]
    vendor_dir = project_root / "rtmp_client" / "vendor" / plat

    if plat == "windows":
        if args.source:
            src_bin = detect_windows_bin_from_ffmpeg(Path(args.source))
        else:
            which = shutil.which("ffmpeg")
            if not which:
                print("ffmpeg tidak ditemukan di PATH. Atau berikan path sumber.")
                return 1
            src_bin = detect_windows_bin_from_ffmpeg(Path(which))
        if not src_bin.exists():
            print(f"Sumber tidak ditemukan: {src_bin}")
            return 1
        copy_windows_bundle(src_bin, vendor_dir)
        print(f"Copied Windows ffmpeg bundle from {src_bin} to {vendor_dir}")
        return 0

    # macOS / Linux
    src_path: Path
    if args.source:
        src_path = Path(args.source)
    else:
        which = shutil.which("ffmpeg")
        if not which:
            print("ffmpeg tidak ditemukan di PATH. Atau berikan path sumber.")
            return 1
        src_path = Path(which)
    if not src_path.exists():
        print(f"Sumber tidak ditemukan: {src_path}")
        return 1
    copy_unix_ffmpeg(src_path, vendor_dir)
    print(f"Copied ffmpeg to {vendor_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
