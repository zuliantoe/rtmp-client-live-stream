from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import json
import os
import platform
import random


APP_NAME = "RTMP Client"
ORG_NAME = "RTMP Client"


def default_config_dir() -> Path:
    home = Path.home()
    system = platform.system().lower()
    if system == "windows":
        base = Path(os.getenv("APPDATA", home / "AppData" / "Roaming"))
        return base / ORG_NAME / APP_NAME
    if system == "darwin":
        return home / "Library" / "Application Support" / APP_NAME
    return home / ".config" / APP_NAME


@dataclass
class AppSettings:
    ffmpeg_path: Optional[str] = None

    # Next steps placeholders
    loop_video: bool = False
    playlist: List[str] = field(default_factory=list)
    shuffle: bool = False

    video_bitrate_kbps: int = 2500
    audio_bitrate_kbps: int = 128
    audio_sample_rate: int = 44100
    target_width: Optional[int] = None
    target_height: Optional[int] = None
    target_fps: Optional[int] = None

    profiles_file: Path = field(default_factory=lambda: default_config_dir() / "profiles.json")
    playlist_file: Path = field(default_factory=lambda: default_config_dir() / "playlist.json")


def ensure_config_dir() -> Path:
    cfg = default_config_dir()
    cfg.mkdir(parents=True, exist_ok=True)
    return cfg


# --- Future helpers (stubs) ---

def shuffle_playlist(files: List[str]) -> List[str]:
    files_copy = list(files)
    random.shuffle(files_copy)
    return files_copy


def save_playlist(path: Path, files: List[str]) -> None:
    ensure_config_dir()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"files": files}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_playlist(path: Path) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("files"), list):
            return [str(x) for x in data["files"]]
    except Exception:
        return []
    return []
