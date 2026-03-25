from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.clients.v12_client import V12Client, utc_now_iso
from app.repositories.risk_repository import RiskRepository


class RiskService:
    SNAPSHOT_TTL_SECONDS = 5.0

    def __init__(self, v12_client: V12Client, risk_repository: RiskRepository) -> None:
        self.v12_client = v12_client
        self.risk_repository = risk_repository
        self._background_refresh_task: asyncio.Task | None = None

    def _empty_snapshot(self) -> dict:
        return {
            'gross_exposure': 0.0,
            'net_exposure': 0.0,
            'leverage': 0.0,
            'drawdown': 0.0,
            'var_95': 0.0,
            'var_1d': 0.0,
            'stress_loss': None,
            'risk_limit': {
                'gross_exposure': 1.0,
                'drawdown': 0.0,
                'max_budget_usage': 1.0,
                'min_fill_rate': 0.85,
                'max_slippage_bps': 10.0,
                'kept_signals': 0,
                'global_alerts': [],
            },
            'concentration': 0.0,
            'kill_switch': 'normal',
            'trading_state': 'running',
            'alert_state': 'unknown',
            'alert': 'unknown',
            'data_status': 'no_data',
            'data_source': 'empty',
            'status_reason': 'snapshot_unavailable',
            'is_stale': True,
            'as_of': utc_now_iso(),
        }

    def _snapshot_is_stale(self, snapshot: dict | None) -> bool:
        if snapshot is None:
            return True
        as_of = snapshot.get('as_of')
        if not as_of:
            return True
        try:
            ts = datetime.fromisoformat(str(as_of).replace('Z', '+00:00'))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            return (datetime.now(timezone.utc) - ts).total_seconds() > self.SNAPSHOT_TTL_SECONDS
        except Exception:
            return True

    def _store_snapshot(self, snapshot: dict) -> dict:
        snapshot['data_status'] = 'ok'
        snapshot['data_source'] = 'live'
        snapshot['status_reason'] = None
        snapshot['is_stale'] = False
        self.risk_repository.insert_snapshot(snapshot)
        return snapshot

    def _snapshot_age_sec(self, snapshot: dict | None) -> float | None:
        if snapshot is None:
            return None
        as_of = snapshot.get('as_of')
        if not as_of:
            return None
        try:
            ts = datetime.fromisoformat(str(as_of).replace('Z', '+00:00'))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            return round(max(0.0, (datetime.now(timezone.utc) - ts).total_seconds()), 3)
        except Exception:
            return None

    def _mark_snapshot(self, snapshot: dict | None, *, data_status: str, data_source: str, status_reason: str | None, is_stale: bool) -> dict:
        if snapshot is None:
            marked = self._empty_snapshot()
        else:
            marked = dict(snapshot)
        marked['data_status'] = data_status
        marked['data_source'] = data_source
        marked['status_reason'] = status_reason
        marked['is_stale'] = is_stale
        return marked

    async def _build_and_store_snapshot(self, *, summary_only: bool = False) -> dict:
        return self._store_snapshot(await self.build_snapshot(summary_only=summary_only))

    def _schedule_background_refresh(self) -> None:
        task = self._background_refresh_task
        if task is not None and not task.done():
            return
        self._background_refresh_task = asyncio.create_task(self._build_and_store_snapshot())
        self._background_refresh_task.add_done_callback(lambda finished: finished.exception())

    async def build_snapshot(self, *, summary_only: bool = False) -> dict:
        risk_budget_task = self.v12_client.get_risk_budget()
        execution_task = self.v12_client.get_execution_quality()
        portfolio_overview_task = self.v12_client.get_portfolio_dashboard()
        if summary_only:
            risk_budget, execution, portfolio_overview = await asyncio.gather(
                risk_budget_task,
                execution_task,
                portfolio_overview_task,
            )
            diagnostics: dict = {}
            positions_payload: dict = {}
        else:
            (
                risk_budget,
                execution,
                diagnostics,
                positions_payload,
                portfolio_overview,
            ) = await asyncio.gather(
                risk_budget_task,
                execution_task,
                self.v12_client.get_portfolio_diagnostics(),
                self.v12_client.get_portfolio_positions(),
                portfolio_overview_task,
            )

        risk = risk_budget.get('risk', {})
        global_risk = risk_budget.get('global', {})
        per_strategy = risk.get('per_strategy', [])
        max_usage = max([float(item.get('budget_usage', 0.0) or 0.0) for item in per_strategy] or [0.0])
        drawdown = max(0.0, round(max_usage - 1.0, 6))
        items = positions_payload.get('items') or positions_payload.get('positions') or []
        latest_snapshot = self.risk_repository.latest_snapshot() if summary_only else None

        weights: list[float] = []
        for row in items:
            weight = float(row.get('weight', row.get('target_weight', 0.0)) or 0.0)
            side = str(row.get('side', 'long') or 'long').lower()
            if side == 'short' and weight > 0:
                weight = -weight
            weights.append(weight)

        summary = portfolio_overview.get("summary") if isinstance(portfolio_overview.get("summary"), dict) else portfolio_overview
        gross = (
            round(sum(abs(w) for w in weights), 6)
            if weights
            else round(float(summary.get("gross_exposure", (latest_snapshot or {}).get("gross_exposure", 0.0)) or 0.0), 6)
        )
        net = (
            round(sum(weights), 6)
            if weights
            else round(float(summary.get("net_exposure", (latest_snapshot or {}).get("net_exposure", 0.0)) or 0.0), 6)
        )
        concentration = (
            max([abs(float(w)) for w in weights] or [0.0])
            if weights
            else float((latest_snapshot or {}).get('concentration', 0.0) or 0.0)
        )
        margin_utilization = float(summary.get("margin_utilization", gross) or gross)
        collateral_equity = float(summary.get("collateral_equity", 0.0) or 0.0)
        available_margin = float(summary.get("available_margin", 0.0) or 0.0)
        fill_rate = execution.get('fill_rate')
        slippage = execution.get('avg_slippage_bps')
        kept_signals = (
            (diagnostics.get('diagnostics') or diagnostics.get('latest') or {}).get('kept_signals', 0)
            if not summary_only
            else int((((latest_snapshot or {}).get('risk_limit') or {}).get('kept_signals', 0) or 0))
        )
        var_95 = round(gross * 0.08, 6)
        risk_limit = {
            "gross_exposure": 1.0,
            "drawdown": 0.10,
            "max_budget_usage": 1.0,
            "min_fill_rate": 0.85,
            "max_slippage_bps": 10.0,
            "kept_signals": 5,
            "global_alerts": [],
        }
        alert_state = 'ok'
        if gross > risk_limit['gross_exposure'] or drawdown > risk_limit['drawdown'] or max_usage > risk_limit['max_budget_usage']:
            alert_state = 'breach'
        elif (fill_rate is not None and float(fill_rate) < risk_limit['min_fill_rate']) or (
            slippage is not None and float(slippage) > risk_limit['max_slippage_bps']
        ):
            alert_state = 'warning'
        if global_risk.get('status') == 'warning' and alert_state == 'ok':
            alert_state = 'warning'
        kill_switch = "triggered" if alert_state == "breach" else "idle"
        trading_state = self.risk_repository.get_trading_state().get('trading_state', 'running')
        if kill_switch == "triggered" and trading_state == "running":
            trading_state = "halted"
        return {
            'gross_exposure': gross,
            'net_exposure': net,
            'leverage': round(max(gross, margin_utilization), 6),
            'drawdown': drawdown,
            'var_95': var_95,
            'var_1d': var_95,
            'stress_loss': None,
            'risk_limit': {**risk_limit, 'kept_signals': kept_signals, 'global_alerts': global_risk.get('alerts', []), 'margin_utilization': margin_utilization, 'collateral_equity': collateral_equity, 'available_margin': available_margin},
            'concentration': round(concentration, 6),
            'kill_switch': 'triggered' if alert_state == 'breach' else 'armed' if alert_state == 'warning' else 'normal',
            'trading_state': trading_state,
            'alert_state': alert_state,
            'alert': alert_state,
            'as_of': positions_payload.get('as_of') or summary.get('as_of') or portfolio_overview.get('as_of') or risk_budget.get('as_of') or execution.get('as_of') or utc_now_iso(),
        }

    async def get_snapshot(self) -> dict:
        latest = self.risk_repository.latest_snapshot()
        if latest is None:
            self._schedule_background_refresh()
            return self._mark_snapshot(None, data_status='no_data', data_source='empty', status_reason='snapshot_unavailable', is_stale=True)
        if not self._snapshot_is_stale(latest):
            return self._mark_snapshot(latest, data_status='ok', data_source='cache', status_reason=None, is_stale=False)
        self._schedule_background_refresh()
        return self._mark_snapshot(latest, data_status='stale', data_source='cache', status_reason='stale_snapshot', is_stale=True)

    async def refresh_snapshot(self, *, summary_only: bool = False) -> dict:
        try:
            return await self._build_and_store_snapshot(summary_only=summary_only)
        except Exception:
            latest = self.risk_repository.latest_snapshot()
            if latest is not None:
                return self._mark_snapshot(latest, data_status='stale', data_source='cache', status_reason='refresh_failed_fallback', is_stale=True)
            return self._mark_snapshot(None, data_status='no_data', data_source='empty', status_reason='snapshot_unavailable', is_stale=True)

    async def get_snapshot_debug(self) -> dict:
        latest = self.risk_repository.latest_snapshot()
        background_refresh_scheduled = False
        if latest is None:
            self._schedule_background_refresh()
            background_refresh_scheduled = True
            payload = self._mark_snapshot(None, data_status='no_data', data_source='empty', status_reason='snapshot_unavailable', is_stale=True)
            read_mode = 'empty_snapshot'
        elif self._snapshot_is_stale(latest):
            self._schedule_background_refresh()
            background_refresh_scheduled = True
            payload = self._mark_snapshot(latest, data_status='stale', data_source='cache', status_reason='stale_snapshot', is_stale=True)
            read_mode = 'stale_cache_read'
        else:
            payload = self._mark_snapshot(latest, data_status='ok', data_source='cache', status_reason=None, is_stale=False)
            read_mode = 'fresh_cache_read'

        trading_state = self.risk_repository.get_trading_state()
        risk_limit = payload.get('risk_limit', {})
        global_alerts = risk_limit.get('global_alerts', []) if isinstance(risk_limit, dict) else []
        return {
            'scope': 'risk.snapshot',
            'status': payload.get('data_status', 'unknown'),
            'source': payload.get('data_source', 'unknown'),
            'reason': payload.get('status_reason'),
            'as_of': payload.get('as_of') or utc_now_iso(),
            'timings': {
                'ttl_sec': self.SNAPSHOT_TTL_SECONDS,
                'snapshot_age_sec': self._snapshot_age_sec(payload),
            },
            'summary': {
                'gross_exposure': payload.get('gross_exposure', 0.0),
                'net_exposure': payload.get('net_exposure', 0.0),
                'leverage': payload.get('leverage', 0.0),
                'drawdown': payload.get('drawdown', 0.0),
                'alert_state': payload.get('alert_state', 'unknown'),
                'kill_switch': payload.get('kill_switch', 'normal'),
                'trading_state': payload.get('trading_state', trading_state.get('trading_state', 'running')),
            },
            'provenance': {
                'read_mode': read_mode,
                'background_refresh_scheduled': background_refresh_scheduled,
                'snapshot_store': 'risk_snapshots',
                'trading_state_store': 'risk_control_state',
                'upstream_dependencies': [
                    'v12:/strategy/risk-budget',
                    'v12:/execution/quality/latest',
                    'v12:/portfolio/diagnostics/latest',
                    'v12:/portfolio/positions/latest',
                    'v12:/portfolio/overview',
                ],
            },
            'counts': {
                'global_alerts': len(global_alerts) if isinstance(global_alerts, list) else 0,
                'configured_kept_signals_limit': int(risk_limit.get('kept_signals', 0) or 0) if isinstance(risk_limit, dict) else 0,
            },
            'raw': {
                'snapshot': payload,
                'trading_state': trading_state,
            },
        }

    async def get_exposure(self) -> dict:
        snapshot = await self.get_snapshot()
        return {
            'gross_exposure': snapshot['gross_exposure'],
            'net_exposure': snapshot['net_exposure'],
            'leverage': snapshot['leverage'],
            'alert_state': snapshot['alert_state'],
            'as_of': snapshot['as_of'],
        }

    async def get_drawdown(self) -> dict:
        snapshot = await self.get_snapshot()
        return {'drawdown': snapshot['drawdown'], 'risk_limit': snapshot['risk_limit'], 'as_of': snapshot['as_of']}
