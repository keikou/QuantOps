from __future__ import annotations

from .common import fetch_json


def check_monitoring() -> None:
    m = fetch_json('/monitoring/system')
    cpu = float(m['cpu'])
    if cpu < 0 or cpu > 1:
        raise AssertionError(f'cpu out of range: {cpu}')
    if float(m['exchange_latency_ms']) < 0:
        raise AssertionError('latency metric invalid')
    if 'worker_status' not in m:
        raise AssertionError('worker_status missing')
