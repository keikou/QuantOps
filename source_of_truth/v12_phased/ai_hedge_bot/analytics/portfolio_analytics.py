from __future__ import annotations

from typing import Any
import json

from ai_hedge_bot.analytics.json_safe import dataframe_records_to_json_safe, to_json_safe
from ai_hedge_bot.data.storage.duckdb_store import DuckDBStore


DROP_PREFIXES = (
    'family_concentration.',
    'selected_count_by_family.',
    'feature_counts.',
)


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except Exception:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _collect_prefixed_map(record: dict[str, Any], prefix: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    prefix_dot = prefix + '.'
    for key, value in list(record.items()):
        if key.startswith(prefix_dot):
            child_key = key[len(prefix_dot):]
            out[child_key] = value
    return out


def _top_family_concentration(family_map: dict[str, Any]) -> float:
    numeric_values: list[float] = []
    for value in family_map.values():
        try:
            numeric_values.append(float(value))
        except Exception:
            continue
    if not numeric_values:
        return 0.0
    return round(max(numeric_values), 6)


def _drop_legacy_flattened_keys(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.items()
        if not any(key.startswith(prefix) for prefix in DROP_PREFIXES)
    }


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)

    family_map = _coerce_mapping(normalized.get('family_concentration'))
    family_map.update(_collect_prefixed_map(normalized, 'family_concentration'))
    if family_map:
        normalized['family_concentration_by_family'] = to_json_safe(family_map)
        normalized['family_concentration'] = _top_family_concentration(family_map)

    selected_family_map = _coerce_mapping(normalized.get('selected_count_by_family'))
    selected_family_map.update(_collect_prefixed_map(normalized, 'selected_count_by_family'))
    if selected_family_map:
        normalized['selected_count_by_family'] = to_json_safe(selected_family_map)

    feature_count_map = _coerce_mapping(normalized.get('feature_counts'))
    feature_count_map.update(_collect_prefixed_map(normalized, 'feature_counts'))
    if feature_count_map:
        normalized['feature_counts'] = to_json_safe(feature_count_map)

    if not str(normalized.get('timestamp', '')).strip() and str(normalized.get('event_time', '')).strip():
        normalized['timestamp'] = normalized['event_time']

    normalized = _drop_legacy_flattened_keys(normalized)
    return to_json_safe(normalized)


def _sort_key(record: dict[str, Any]) -> tuple[int, str]:
    timestamp = str(record.get('timestamp', '') or '').strip()
    event_time = str(record.get('event_time', '') or '').strip()
    sort_value = timestamp or event_time
    return (0 if sort_value else 1, sort_value)


def _has_effective_timestamp(record: dict[str, Any]) -> bool:
    timestamp = str(record.get('timestamp', '') or '').strip()
    event_time = str(record.get('event_time', '') or '').strip()
    return bool(timestamp or event_time)


def load_portfolio_diagnostics(store: DuckDBStore) -> list[dict]:
    try:
        df = store.query_df('select * from portfolio_diagnostics').fillna('')
        records = dataframe_records_to_json_safe(df)
        normalized = [_normalize_record(record) for record in records]
        dated = [record for record in normalized if _has_effective_timestamp(record)]
        sortable = dated if dated else normalized
        return sorted(sortable, key=_sort_key, reverse=True)
    except Exception:
        return []
