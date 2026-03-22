from __future__ import annotations


def build_execution_plan(decisions: list[dict]) -> dict:
    return {'orders': decisions, 'status': 'planned'}
