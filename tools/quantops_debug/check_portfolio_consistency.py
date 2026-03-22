from __future__ import annotations

from .common import fetch_json


def _extract_positions(payload: dict) -> list[dict]:
    if isinstance(payload, list):
        return payload
    return payload.get('items') or payload.get('positions') or []


def check_portfolio() -> None:
    portfolio = fetch_json('/portfolio/overview')
    risk = fetch_json('/risk/snapshot')
    dashboard = fetch_json('/dashboard/overview')
    positions_payload = fetch_json('/portfolio/positions')
    positions = _extract_positions(positions_payload)

    p = float(portfolio['net_exposure'])
    r = float(risk['net_exposure'])
    d = float(dashboard['net_exposure'])

    if not (abs(p - r) < 1e-6 and abs(p - d) < 1e-6):
        raise AssertionError(f'Exposure mismatch portfolio={p} risk={r} dashboard={d}')

    for row in positions:
        for key in ('symbol', 'side', 'quantity', 'avg_price', 'mark_price'):
            if key not in row:
                raise AssertionError(f'missing position field {key} in {row}')
