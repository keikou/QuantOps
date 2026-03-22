from __future__ import annotations

import os
from typing import Any

import requests

API_BASE = os.getenv('QUANTOPS_DEBUG_BASE_URL', 'http://localhost:8010').rstrip('/')
PREFIX = os.getenv('QUANTOPS_DEBUG_API_PREFIX', '/api/v1')
TIMEOUT = float(os.getenv('QUANTOPS_DEBUG_TIMEOUT_SEC', '5'))


def fetch_json(path: str) -> Any:
    url = f"{API_BASE}{PREFIX}{path}"
    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def post_json(path: str, payload: dict | None = None) -> Any:
    url = f"{API_BASE}{PREFIX}{path}"
    response = requests.post(url, json=payload or {}, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()
