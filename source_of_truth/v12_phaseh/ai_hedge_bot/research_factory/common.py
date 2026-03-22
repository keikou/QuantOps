from __future__ import annotations

import json
from typing import Any


def parse_json_field(value: str | None, default: Any) -> Any:
    if value in (None, ''):
        return default
    try:
        return json.loads(value)
    except Exception:
        return default
