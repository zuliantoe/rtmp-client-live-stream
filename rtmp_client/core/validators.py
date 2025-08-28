from __future__ import annotations

import os
from urllib.parse import urlparse


def is_file_readable(path: str) -> bool:
    if not path:
        return False
    if not os.path.isfile(path):
        return False
    try:
        with open(path, "rb"):
            return True
    except Exception:
        return False


def is_valid_rtmp_url(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"rtmp", "rtmps"} and bool(parsed.netloc)
