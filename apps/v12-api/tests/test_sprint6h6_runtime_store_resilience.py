from pathlib import Path

from ai_hedge_bot.data.storage.runtime_store import RuntimeStore


def test_runtime_store_reuses_session_without_reopening(tmp_path: Path):
    store = RuntimeStore(tmp_path / 'analytics.duckdb')
    store.append('runtime_runs', {
        'run_id': 'r1',
        'job_name': 'paper',
        'mode': 'paper',
        'started_at': '2026-03-19T00:00:00Z',
        'finished_at': '2026-03-19T00:00:01Z',
        'status': 'ok',
        'error_message': None,
        'duration_ms': 1000,
        'triggered_by': 'test',
        'created_at': '2026-03-19T00:00:01Z',
    })
    row1 = store.fetchone_dict('SELECT run_id FROM runtime_runs LIMIT 1')
    row2 = store.fetchone_dict('SELECT run_id FROM runtime_runs LIMIT 1')
    assert row1 == {'run_id': 'r1'}
    assert row2 == {'run_id': 'r1'}
    store.close()
