from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.core.utils import utc_now

PREFIXES = (
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


def _collect_prefixed_map(row: dict[str, Any], prefix: str) -> dict[str, Any]:
    collected: dict[str, Any] = {}
    prefix_dot = prefix + '.'
    for key, value in row.items():
        if key.startswith(prefix_dot):
            collected[key[len(prefix_dot):]] = value
    return collected


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)

    for prefix in ('family_concentration', 'selected_count_by_family', 'feature_counts'):
        combined = _coerce_mapping(normalized.get(prefix))
        combined.update(_collect_prefixed_map(normalized, prefix))
        if combined:
            normalized[prefix] = combined

    for key in list(normalized.keys()):
        if any(key.startswith(prefix) for prefix in PREFIXES):
            normalized.pop(key, None)

    if not str(normalized.get('timestamp', '')).strip():
        normalized['timestamp'] = normalized.get('event_time') or utc_now().isoformat()

    return normalized


def cleanup_file(path: Path) -> int:
    if not path.exists():
        return 0
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        rows.append(normalize_row(json.loads(line)))
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    return len(rows)


def main() -> None:
    path = SETTINGS.log_dir / 'portfolio_diagnostics.jsonl'
    count = cleanup_file(path)
    print(json.dumps({'cleaned_rows': count, 'path': str(path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
