from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None


def to_json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if np is not None:
        if isinstance(value, np.generic):
            return value.item()
    if isinstance(value, dict):
        return {str(k): to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_safe(v) for v in value]
    if hasattr(value, 'to_pydatetime'):
        try:
            return value.to_pydatetime().isoformat()
        except Exception:
            pass
    if hasattr(value, 'item'):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


def dataframe_records_to_json_safe(df: Any) -> list[dict[str, Any]]:
    records = df.to_dict(orient='records')
    return [to_json_safe(record) for record in records]
