from __future__ import annotations

from .common import fetch_json


def check_dashboard() -> None:
    dash = fetch_json('/dashboard/overview')
    port = fetch_json('/portfolio/overview')

    if abs(float(dash['net_exposure']) - float(port['net_exposure'])) > 1e-6:
        raise AssertionError('dashboard exposure mismatch')
    if int(dash.get('active_strategies', 0)) <= 0:
        raise AssertionError('active_strategies invalid')
