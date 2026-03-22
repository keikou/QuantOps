from __future__ import annotations

from .common import fetch_json


def check_execution() -> None:
    fills = fetch_json('/analytics/execution-latest')
    positions_payload = fetch_json('/portfolio/positions')
    summary = fetch_json('/analytics/execution-summary')

    fill_rows = fills.get('items') if isinstance(fills, dict) else fills
    pos_rows = positions_payload.get('items') if isinstance(positions_payload, dict) else positions_payload
    fill_rows = fill_rows or []
    pos_rows = pos_rows or []

    fill_symbols = {f['symbol'] for f in fill_rows if f.get('symbol')}
    pos_symbols = {p['symbol'] for p in pos_rows if p.get('symbol')}

    if pos_symbols and not pos_symbols.issubset(fill_symbols):
        raise AssertionError(f'positions without fills: {sorted(pos_symbols - fill_symbols)}')

    for key in ('fill_rate', 'avg_slippage_bps', 'latency_ms_p50', 'venue_score'):
        if key not in summary:
            raise AssertionError(f'missing execution summary key {key}')
