from __future__ import annotations

from datetime import datetime, timezone
import hashlib


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_id(prefix: str, seed: str) -> str:
    digest = hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]
    return f"{prefix}_{digest}"
