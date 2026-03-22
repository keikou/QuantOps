from __future__ import annotations

from functools import lru_cache

from app.clients.v12_client import V12Client


@lru_cache(maxsize=1)
def get_v12_client() -> V12Client:
    return V12Client()
