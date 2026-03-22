from __future__ import annotations

from .common import fetch_json


def check_alerts() -> None:
    risk = fetch_json('/risk/snapshot')
    alerts = fetch_json('/alerts')
    if risk.get('alert_state') == 'breach' and int(alerts.get('count', 0)) <= 0:
        raise AssertionError('risk breach exists but no alerts present')
