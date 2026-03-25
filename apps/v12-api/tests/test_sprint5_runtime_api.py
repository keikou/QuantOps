from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.api.routes import portfolio as portfolio_routes
from ai_hedge_bot.api.routes import risk as risk_routes
from ai_hedge_bot.api.routes import runtime as runtime_routes
from ai_hedge_bot.api.routes import strategy as strategy_routes

client = TestClient(app)


def _reset_runtime_tables() -> None:
    tables = [
        'runtime_control_state', 'execution_state_snapshots', 'execution_block_reasons',
        'runtime_runs', 'runtime_run_steps', 'scheduler_runs', 'runtime_checkpoints', 'audit_logs',
        'signals', 'signal_evaluations', 'alpha_signal_snapshots', 'alpha_candidates',
        'portfolio_signal_decisions', 'portfolio_diagnostics', 'portfolio_snapshots', 'portfolio_positions', 'rebalance_plans',
        'execution_plans', 'execution_fills', 'execution_quality_snapshots', 'shadow_orders', 'shadow_fills', 'shadow_pnl_snapshots',
        'orchestrator_runs', 'orchestrator_cycles',
    ]
    for table in tables:
        CONTAINER.runtime_store.execute(f'DELETE FROM {table}')


def test_runtime_run_once_persists_full_pipeline() -> None:
    from ai_hedge_bot.api.routes import execution as execution_routes

    execution_routes._execution_quality_summary_cache['expires_at'] = None
    execution_routes._execution_quality_summary_cache['payload'] = None
    _reset_runtime_tables()
    response = client.post('/runtime/run-once')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    run_id = payload['run_id']

    detail = client.get(f'/runtime/runs/{run_id}')
    assert detail.status_code == 200
    item = detail.json()['item']
    assert item['status'] == 'success'
    assert len(item['steps']) == 1
    assert len(item['checkpoints']) == 1
    assert len(item['audit_logs']) >= 3

    signal_snapshot = client.get('/strategy/signals/latest').json()
    assert signal_snapshot['snapshot']['run_id'] == run_id
    assert signal_snapshot['snapshot']['signal_count'] > 0
    assert len(signal_snapshot['items']) == signal_snapshot['snapshot']['signal_count']

    portfolio = client.get('/portfolio/overview').json()
    assert portfolio['snapshot']['run_id'] == run_id
    assert portfolio['snapshot']['target_count'] == len(portfolio['positions'])
    assert portfolio['snapshot']['gross_exposure'] > 0

    execution = client.get('/execution/quality/latest').json()
    assert execution['run_id'] == run_id
    assert execution['order_count'] == execution['fill_count']
    assert len(execution['latest_fills']) == execution['fill_count']

    summary = client.get('/execution/quality/latest_summary').json()
    assert summary['run_id'] == run_id
    assert summary['order_count'] == execution['order_count']
    assert summary['fill_count'] == execution['fill_count']
    assert 'latest_fills' not in summary
    assert 'latest_plans' not in summary


def test_scheduler_routes_show_seeded_jobs_and_runs() -> None:
    _reset_runtime_tables()
    client.post('/runtime/run-once')
    jobs = client.get('/scheduler/jobs')
    assert jobs.status_code == 200
    assert len(jobs.json()['items']) >= 2

    runs = client.get('/scheduler/runs')
    assert runs.status_code == 200
    assert len(runs.json()['items']) >= 1


def test_runtime_runs_route_reuses_short_ttl_cache(monkeypatch) -> None:
    runtime_routes._runtime_runs_cache.clear()
    call_count = {'count': 0}

    def fake_list_runs(*, limit: int = 20) -> list[dict]:
        call_count['count'] += 1
        return [{'run_id': f'run-{call_count["count"]}', 'created_at': '2026-03-23T00:00:00Z'}]

    monkeypatch.setattr(runtime_routes._service, 'list_runs', fake_list_runs)

    first = client.get('/runtime/runs?limit=5')
    second = client.get('/runtime/runs?limit=5')
    third = client.get('/runtime/runs?limit=10')

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert first.json()['items'] == second.json()['items']
    assert first.json()['items'] != third.json()['items']
    assert call_count['count'] == 2


def test_portfolio_equity_history_reuses_short_ttl_cache_by_limit(monkeypatch) -> None:
    portfolio_routes._equity_history_cache.clear()
    call_count = {'count': 0}

    def fake_fetchall_dict(query: str, params=None):
        call_count['count'] += 1
        limit = int((params or [0])[0] or 0)
        return [
            {
                'snapshot_time': f'2026-03-24T00:00:{limit:02d}+00:00',
                'total_equity': float(limit),
                'pnl': float(limit) / 10.0,
                'drawdown': 0.0,
            }
        ]

    monkeypatch.setattr(CONTAINER.runtime_store, 'fetchall_dict', fake_fetchall_dict)

    first = client.get('/portfolio/equity-history?limit=20')
    second = client.get('/portfolio/equity-history?limit=20')
    third = client.get('/portfolio/equity-history?limit=10')

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert first.json() == second.json()
    assert first.json() != third.json()
    assert call_count['count'] == 2


def test_portfolio_equity_history_live_bypasses_cache(monkeypatch) -> None:
    portfolio_routes._equity_history_cache.clear()
    call_count = {'count': 0}

    def fake_fetchall_dict(query: str, params=None):
        call_count['count'] += 1
        return [
            {
                'snapshot_time': f'2026-03-24T00:00:0{call_count["count"]}+00:00',
                'total_equity': 100.0 + call_count['count'],
                'pnl': 1.0,
                'drawdown': 0.0,
            }
        ]

    monkeypatch.setattr(CONTAINER.runtime_store, 'fetchall_dict', fake_fetchall_dict)

    cached = client.get('/portfolio/equity-history?limit=20')
    live = client.get('/portfolio/equity-history/live?limit=20')

    assert cached.status_code == 200
    assert live.status_code == 200
    assert cached.json() != live.json()
    assert call_count['count'] == 2


def test_portfolio_metrics_latest_reuses_short_ttl_cache(monkeypatch) -> None:
    portfolio_routes._portfolio_metrics_cache['expires_at'] = None
    portfolio_routes._portfolio_metrics_cache['payload'] = None
    call_count = {'count': 0}

    def fake_builder(limit: int = 60) -> dict:
        call_count['count'] += 1
        return {
            'status': 'ok',
            'fill_rate': 0.5,
            'expected_sharpe': 1.25,
            'expected_volatility': 0.12,
            'as_of': f'2026-03-24T00:00:0{call_count["count"]}+00:00',
            'source_snapshot_time': f'2026-03-24T00:00:0{call_count["count"]}+00:00',
            'build_status': 'live',
            'equity_history_limit': limit,
        }

    monkeypatch.setattr(portfolio_routes, '_build_portfolio_metrics_payload', fake_builder)

    first = client.get('/portfolio/metrics/latest?limit=60')
    second = client.get('/portfolio/metrics/latest?limit=60')

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()['expected_sharpe'] == second.json()['expected_sharpe']
    assert second.json()['build_status'] == 'fresh_cache'
    assert call_count['count'] == 1


def test_execution_bridge_latest_reuses_short_ttl_cache(monkeypatch) -> None:
    from ai_hedge_bot.api.routes import execution as execution_routes

    execution_routes._execution_bridge_cache['expires_at'] = None
    execution_routes._execution_bridge_cache['payload'] = None
    call_count = {'count': 0}

    def fake_bridge_summary() -> dict:
        call_count['count'] += 1
        return {
            'status': 'ok',
            'run_id': f'run-{call_count["count"]}',
            'cycle_id': f'cycle-{call_count["count"]}',
            'bridge_state': 'filled',
            'planned_count': 2,
            'submitted_count': 2,
            'blocked_count': 0,
            'filled_count': 2,
            'event_chain_complete': True,
            'latest_reason_code': None,
            'latest_reason_summary': None,
            'blocking_component': None,
            'degraded_flags': [],
            'operator_message': 'ok',
            'last_transition_at': f'2026-03-24T00:00:0{call_count["count"]}+00:00',
        }

    monkeypatch.setattr(execution_routes._bridge, 'get_bridge_summary', fake_bridge_summary)

    first = client.get('/execution/bridge/latest')
    second = client.get('/execution/bridge/latest')

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()['run_id'] == second.json()['run_id']
    assert first.json()['build_status'] == 'live'
    assert second.json()['build_status'] == 'fresh_cache'
    assert call_count['count'] == 1


def test_runtime_status_reuses_short_ttl_cache(monkeypatch) -> None:
    runtime_routes._runtime_status_cache = None
    call_count = {'runs': 0, 'state': 0, 'query': 0, 'bridge': 0}

    def fake_list_runs(*, limit: int = 1) -> list[dict]:
        call_count['runs'] += 1
        return [{'run_id': f'run-{call_count["runs"]}', 'created_at': '2026-03-24T00:00:00+00:00'}]

    def fake_trading_state() -> dict:
        call_count['state'] += 1
        return {'trading_state': 'running', 'note': f'note-{call_count["state"]}'}

    def fake_fetchone_dict(query: str, params=None):
        call_count['query'] += 1
        if 'portfolio_positions' in query:
            return {'run_id': 'run-1', 'created_at': '2026-03-24T00:00:00+00:00', 'position_count': 3}
        if 'signals' in query:
            return {'created_at': '2026-03-24T00:00:00+00:00', 'signal_count': 7}
        if 'execution_quality_snapshots' in query:
            return {'created_at': '2026-03-24T00:00:00+00:00', 'fill_count': 2, 'order_count': 2}
        return None

    def fake_bridge_summary() -> dict:
        call_count['bridge'] += 1
        return {
            'run_id': 'run-1',
            'cycle_id': 'cycle-1',
            'bridge_state': 'submitted_no_fill',
            'planned_count': 2,
            'submitted_count': 2,
            'blocked_count': 0,
            'filled_count': 0,
            'event_chain_complete': True,
            'latest_reason_code': 'ORDER_REJECTED',
            'latest_reason_summary': 'Orders submitted but no fills were recorded.',
            'blocking_component': 'execution_bridge',
            'degraded_flags': ['stale_market_data'],
            'operator_message': 'The cycle reached the market but did not fill.',
            'last_transition_at': '2026-03-24T00:00:00+00:00',
            'source_snapshot_time': '2026-03-24T00:00:00+00:00',
            'build_status': 'live',
        }

    monkeypatch.setattr(runtime_routes._service, 'list_runs', fake_list_runs)
    monkeypatch.setattr(runtime_routes._service, 'get_trading_state', fake_trading_state)
    monkeypatch.setattr(CONTAINER.runtime_store, 'fetchone_dict', fake_fetchone_dict)
    monkeypatch.setattr(runtime_routes, '_runtime_status_bridge_summary', fake_bridge_summary)

    first = client.get('/runtime/status')
    second = client.get('/runtime/status')

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()['run_id'] == second.json()['run_id']
    assert first.json()['build_status'] == 'live'
    assert second.json()['build_status'] == 'fresh_cache'
    assert call_count['runs'] == 1
    assert call_count['state'] == 1
    assert call_count['bridge'] == 1
    assert first.json()['bridge_state'] == 'submitted_no_fill'


def test_risk_latest_reuses_short_ttl_cache(monkeypatch) -> None:
    risk_routes._risk_latest_cache["expires_at"] = None
    risk_routes._risk_latest_cache["payload"] = None
    call_count = {"count": 0}

    def fake_latest_risk() -> dict:
        call_count["count"] += 1
        return {"status": "ok", "risk": {"run_id": f"run-{call_count['count']}"}}

    monkeypatch.setattr(CONTAINER.sprint5c_service, "get_latest_risk", fake_latest_risk)

    first = client.get('/risk/latest')
    second = client.get('/risk/latest')

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["risk"]["run_id"] == second.json()["risk"]["run_id"]
    assert first.json()["build_status"] == "live"
    assert second.json()["build_status"] == "fresh_cache"
    assert call_count["count"] == 1


def test_strategy_risk_budget_reuses_short_ttl_cache(monkeypatch) -> None:
    strategy_routes._risk_budget_cache["expires_at"] = None
    strategy_routes._risk_budget_cache["payload"] = None
    call_count = {"count": 0}

    def fake_latest_risk_budget() -> dict:
        call_count["count"] += 1
        return {"status": "ok", "risk": {"run_id": f"run-{call_count['count']}"}, "global": {}}

    monkeypatch.setattr(strategy_routes._service, "latest_risk_budget", fake_latest_risk_budget)

    first = client.get('/strategy/risk-budget')
    second = client.get('/strategy/risk-budget')

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["risk"]["run_id"] == second.json()["risk"]["run_id"]
    assert first.json()["build_status"] == "live"
    assert second.json()["build_status"] == "fresh_cache"
    assert call_count["count"] == 1


def test_portfolio_positions_latest_reuses_short_ttl_cache(monkeypatch) -> None:
    portfolio_routes._portfolio_positions_cache["expires_at"] = None
    portfolio_routes._portfolio_positions_cache["payload"] = None
    call_count = {"count": 0}

    def fake_overview() -> dict:
        call_count["count"] += 1
        return {
            "summary": {"total_equity": 1000.0, "as_of": "2026-03-24T00:00:00+00:00"},
            "snapshot": {"run_id": f"run-{call_count['count']}", "created_at": "2026-03-24T00:00:00+00:00"},
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "exposure_notional": 100.0,
                    "unrealized_pnl": 5.0,
                    "abs_qty": 0.1,
                    "avg_entry_price": 50000.0,
                    "mark_price": 51000.0,
                    "strategy_id": "trend_core",
                    "alpha_family": "trend",
                    "price_source": "mark",
                    "quote_time": "2026-03-24T00:00:00+00:00",
                    "quote_age_sec": 0.5,
                    "stale": False,
                }
            ],
        }

    monkeypatch.setattr(portfolio_routes._repo, "latest_portfolio_overview", fake_overview)

    first = client.get("/portfolio/positions/latest")
    second = client.get("/portfolio/positions/latest")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["run_id"] == second.json()["run_id"]
    assert first.json()["build_status"] == "live"
    assert second.json()["build_status"] == "fresh_cache"
    assert call_count["count"] == 1


def test_portfolio_diagnostics_latest_reuses_short_ttl_cache(monkeypatch) -> None:
    portfolio_routes._portfolio_diagnostics_cache["expires_at"] = None
    portfolio_routes._portfolio_diagnostics_cache["payload"] = None
    monkeypatch.setattr(
        portfolio_routes.CONTAINER,
        "latest_portfolio_diagnostics",
        {"kept_signals": 3, "input_signals": 5, "crowding_flags": [], "overlap_penalty_applied": False},
    )

    first = client.get("/portfolio/diagnostics/latest")
    second = client.get("/portfolio/diagnostics/latest")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["build_status"] == "live"
    assert second.json()["build_status"] == "fresh_cache"
