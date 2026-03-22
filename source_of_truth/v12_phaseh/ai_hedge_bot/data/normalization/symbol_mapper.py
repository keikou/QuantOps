from __future__ import annotations


def map_symbol(symbol: str) -> str:
    return str(symbol).upper().replace('-', '').replace('/', '')
