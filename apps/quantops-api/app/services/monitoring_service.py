from __future__ import annotations

import asyncio
import os
import shutil
import inspect
from pathlib import Path
from datetime import datetime, timezone

from app.clients.v12_client import V12Client, utc_now_iso
from app.repositories.monitoring_repository import MonitoringRepository


class MonitoringService:
    SNAPSHOT_TTL_SECONDS = 5.0

    def __init__(self, v12_client: V12Client, repository: MonitoringRepository) -> None:
        self.v12_client = v12_client
        self.repository = repository
        self._background_refresh_task: asyncio.Task | None = None

    async def _call_client_dict(self, method_name: str) -> dict:
        method = getattr(self.v12_client, method_name, None)
        if method is None or not callable(method):
            return {}
        try:
            result = method()
            for _ in range(4):
                if inspect.isawaitable(result):
                    result = await result
                else:
                    break
            return result if isinstance(result, dict) else {}
        except Exception:
            return {}

    def _cpu_fraction(self) -> float:
        try:
            load1 = os.getloadavg()[0]
            cpu_count = os.cpu_count() or 1
            return max(0.0, min(load1 / max(cpu_count, 1), 1.0))
        except Exception:
            return 0.0

    def _memory_fraction(self) -> float:
        meminfo = Path('/proc/meminfo')
        if not meminfo.exists():
            return 0.0
        try:
            values: dict[str, float] = {}
            for line in meminfo.read_text().splitlines():
                parts = line.split(':', 1)
                if len(parts) != 2:
                    continue
                key = parts[0].strip()
                value = parts[1].strip().split()[0]
                values[key] = float(value)
            total = values.get('MemTotal', 0.0)
            available = values.get('MemAvailable', values.get('MemFree', 0.0))
            if total <= 0:
                return 0.0
            return max(0.0, min((total - available) / total, 1.0))
        except Exception:
            return 0.0

    def _disk_status(self, path_hint: str | None) -> tuple[str, bool]:
        try:
            path = Path(path_hint or '.').resolve()
            usage = shutil.disk_usage(path)
            free_ratio = usage.free / max(usage.total, 1)
            status = 'ok' if free_ratio > 0.15 else 'low'
            writable = os.access(path, os.W_OK)
            return status, bool(writable)
        except Exception:
            return 'unknown', False

    def _data_freshness_sec(self, as_of: str | None) -> float:
        ts = self._parse_ts(as_of)
        if ts is None:
            return 0.0
        now = datetime.now(timezone.utc)
        return max(0.0, (now - ts).total_seconds())

    def _parse_ts(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            ts = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            return ts
        except Exception:
            return None

    def _snapshot_is_stale(self, payload: dict | None, max_age_sec: float = 5.0) -> bool:
        if not payload:
            return True
        as_of = payload.get('as_of')
        ts = self._parse_ts(as_of)
        if ts is None:
            return True
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return age > max_age_sec

    def _snapshot_age_sec(self, payload: dict | None) -> float | None:
        if not payload:
            return None
        ts = self._parse_ts(payload.get('as_of'))
        if ts is None:
            return None
        return round(max(0.0, (datetime.now(timezone.utc) - ts).total_seconds()), 3)

    def _empty_snapshot(self) -> dict:
        as_of = utc_now_iso()
        return {
            'system_status': 'unknown',
            'execution_status': 'unknown',
            'services': {},
            'system': {},
            'execution': {},
            'planner': {},
            'execution_state': {},
            'block_reasons': [],
            'runtime': {},
            'cpu': 0.0,
            'memory': 0.0,
            'disk': 'unknown',
            'db_writable': False,
            'exchange_latency_ms': 0.0,
            'data_freshness_sec': 0.0,
            'exchange': '',
            'latency_ms': 0.0,
            'queue': 0,
            'worker_status': 'unknown',
            'execution_state_name': '',
            'execution_reason': None,
            'risk_trading_state': 'running',
            'kill_switch': 'normal',
            'alert_state': 'unknown',
            'data_status': 'no_data',
            'data_source': 'empty',
            'status_reason': 'snapshot_unavailable',
            'is_stale': True,
            'last_activity_as_of': None,
            'heartbeat_age_sec': None,
            'as_of': as_of,
        }

    def _schedule_background_refresh(self) -> None:
        task = self._background_refresh_task
        if task is not None and not task.done():
            return
        self._background_refresh_task = asyncio.create_task(self.refresh())
        self._background_refresh_task.add_done_callback(lambda finished: finished.exception())

    def _mark_snapshot(self, payload: dict | None, *, data_status: str, data_source: str, status_reason: str | None, is_stale: bool) -> dict:
        marked = dict(payload) if payload is not None else self._empty_snapshot()
        marked['data_status'] = data_status
        marked['data_source'] = data_source
        marked['status_reason'] = status_reason
        marked['is_stale'] = is_stale
        return marked

    def _worker_activity(self, runtime: dict, execution: dict, health: dict, planner: dict | None = None, execution_state: dict | None = None) -> tuple[str, str | None, float | None]:
        execution_ts = self._parse_ts(runtime.get('latest_execution_timestamp') or (execution_state or {}).get('as_of'))
        planner_ts = self._parse_ts((planner or {}).get('latest_activity_at') or (planner or {}).get('as_of'))
        heartbeat_ts = self._parse_ts(runtime.get('latest_run_timestamp') or runtime.get('as_of') or health.get('as_of'))
        now = datetime.now(timezone.utc)
        execution_age = max(0.0, (now - execution_ts).total_seconds()) if execution_ts else None
        planner_age = max(0.0, (now - planner_ts).total_seconds()) if planner_ts else None
        heartbeat_age = max(0.0, (now - heartbeat_ts).total_seconds()) if heartbeat_ts else None
        last_fill_age = (execution_state or {}).get('last_fill_age_sec')
        try:
            last_fill_age = float(last_fill_age) if last_fill_age is not None else None
        except Exception:
            last_fill_age = None
        active_plan_count = int((execution_state or {}).get('active_plan_count', 0) or 0)
        open_order_count = int((execution_state or {}).get('open_order_count', 0) or 0)
        submitted_order_count = int((execution_state or {}).get('submitted_order_count', 0) or 0)
        planner_count = int((planner or {}).get('plan_count', 0) or 0)
        state_name = str((execution_state or {}).get('execution_state', '') or '').lower()
        if state_name in {'halted', 'blocked'}:
            return state_name, (execution_ts or planner_ts or heartbeat_ts).isoformat() if (execution_ts or planner_ts or heartbeat_ts) else None, round(execution_age or planner_age or heartbeat_age or 0.0, 3)
        last = execution_ts or planner_ts or heartbeat_ts
        if last is None:
            return 'idle', None, None
        recent_fill = last_fill_age is not None and last_fill_age <= 120.0
        recent_exec = execution_age is not None and execution_age <= 120.0
        recent_plan = planner_age is not None and planner_age <= 120.0
        recent_heartbeat = heartbeat_age is not None and heartbeat_age <= 120.0
        if recent_fill or recent_exec or (recent_plan and (active_plan_count > 0 or planner_count > 0)) or (recent_heartbeat and (open_order_count > 0 or submitted_order_count > 0)):
            return 'running', last.isoformat(), round(min([x for x in [execution_age, planner_age, heartbeat_age] if x is not None] or [0.0]), 3)
        if open_order_count > 0 or submitted_order_count > 0 or active_plan_count > 0:
            ref_age = execution_age if execution_age is not None else planner_age if planner_age is not None else heartbeat_age
            return 'degraded', last.isoformat(), round(ref_age or 0.0, 3)
        if recent_heartbeat:
            return 'idle', last.isoformat(), round(heartbeat_age or 0.0, 3)
        return 'dead', last.isoformat(), round(max([x for x in [execution_age, planner_age, heartbeat_age] if x is not None] or [0.0]), 3)

    async def refresh(self) -> dict:
        (
            health,
            execution,
            runtime,
            planner,
            execution_state,
            block_reasons,
            risk,
            risk_snapshot,
        ) = await asyncio.gather(
            self._call_client_dict('get_system_health'),
            self._call_client_dict('get_execution_quality'),
            self._call_client_dict('get_runtime_status'),
            self._call_client_dict('get_execution_planner_latest'),
            self._call_client_dict('get_execution_state_latest'),
            self._call_client_dict('get_execution_block_reasons_latest'),
            self._call_client_dict('get_risk_budget'),
            self._call_client_dict('get_sprint5c_risk_latest'),
        )

        db_path = getattr(getattr(self.repository, 'factory', None), 'db_path', None)
        disk, db_writable = self._disk_status(Path(db_path).parent if db_path else '.')
        as_of = runtime.get('as_of') or execution.get('as_of') or planner.get('as_of') or health.get('as_of') or utc_now_iso()
        worker_status, last_activity_as_of, heartbeat_age_sec = self._worker_activity(runtime, execution, health, planner, execution_state)
        if str(execution_state.get('execution_state', '')).lower() in {'blocked', 'halted'}:
            worker_status = str(execution_state.get('execution_state')).lower()
        elif (block_reasons.get('items') or execution_state.get('block_reasons')) and worker_status == 'running':
            worker_status = 'degraded'
        risk_info = risk_snapshot if isinstance(risk_snapshot, dict) and risk_snapshot else (risk if isinstance(risk, dict) else {})
        trading_state = str((risk_info.get('trading_state') or execution_state.get('trading_state') or 'running'))
        kill_switch = str((risk_info.get('kill_switch') or 'normal'))
        payload = {
            'system_status': health.get('status', 'unknown'),
            'execution_status': execution.get('status', 'unknown'),
            'services': health.get('services', {}),
            'system': health,
            'execution': execution,
            'planner': planner,
            'execution_state': execution_state,
            'block_reasons': block_reasons.get('items', execution_state.get('block_reasons', [])),
            'runtime': runtime,
            'cpu': round(self._cpu_fraction(), 6),
            'memory': round(self._memory_fraction(), 6),
            'disk': disk,
            'db_writable': db_writable,
            'exchange_latency_ms': float(execution.get('latency_ms_p50', execution.get('latency_ms', 0.0)) or 0.0),
            'data_freshness_sec': round(self._data_freshness_sec(runtime.get('as_of') or execution.get('as_of') or planner.get('as_of')), 3),
            'exchange': str((health.get('services') or {}).get('exchange', 'connected')),
            'latency_ms': float(execution.get('latency_ms_p95', execution.get('latency_ms', 0.0)) or 0.0),
            'queue': int(planner.get('plan_count', 0) or 0),
            'worker_status': worker_status,
            'execution_state_name': execution_state.get('execution_state'),
            'execution_reason': execution_state.get('reason') or ((execution_state.get('block_reasons') or [{}])[0].get('code') if execution_state.get('block_reasons') else None),
            'risk_trading_state': trading_state,
            'kill_switch': kill_switch,
            'alert_state': str(risk_info.get('alert_state') or risk_info.get('alert') or 'unknown'),
            'data_status': 'ok',
            'data_source': 'live',
            'status_reason': None,
            'is_stale': False,
            'last_activity_as_of': last_activity_as_of,
            'heartbeat_age_sec': heartbeat_age_sec,
            'as_of': as_of,
        }
        return self.repository.insert_snapshot(payload)

    async def get_system(self) -> dict:
        payload = self.repository.latest_snapshot()
        if payload is None:
            self._schedule_background_refresh()
            payload = self._mark_snapshot(None, data_status='no_data', data_source='empty', status_reason='snapshot_unavailable', is_stale=True)
        elif self._snapshot_is_stale(payload, self.SNAPSHOT_TTL_SECONDS):
            self._schedule_background_refresh()
            payload = self._mark_snapshot(payload, data_status='stale', data_source='cache', status_reason='stale_snapshot', is_stale=True)
        else:
            payload = self._mark_snapshot(payload, data_status='ok', data_source='cache', status_reason=None, is_stale=False)
        return {
            'status': payload.get('system_status', 'unknown'),
            'services': payload.get('services', {}),
            'cpu': float(payload.get('cpu', 0.0) or 0.0),
            'memory': float(payload.get('memory', 0.0) or 0.0),
            'disk': payload.get('disk', 'unknown'),
            'db_writable': bool(payload.get('db_writable', False)),
            'exchange_latency_ms': float(payload.get('exchange_latency_ms', 0.0) or 0.0),
            'data_freshness_sec': float(payload.get('data_freshness_sec', 0.0) or 0.0),
            'exchange': payload.get('exchange', ''),
            'latency_ms': float(payload.get('latency_ms', 0.0) or 0.0),
            'queue': int(payload.get('queue', 0) or 0),
            'worker_status': payload.get('worker_status', 'unknown'),
            'executionState': payload.get('execution_state_name', payload.get('execution_state', {}).get('execution_state', '')),
            'executionReason': payload.get('execution_reason', payload.get('execution_state', {}).get('reason', '')),
            'execution_state': payload.get('execution_state', {}),
            'block_reasons': payload.get('block_reasons', []),
            'riskTradingState': payload.get('risk_trading_state', 'running'),
            'killSwitch': payload.get('kill_switch', 'normal'),
            'alertState': payload.get('alert_state', 'unknown'),
            'dataStatus': payload.get('data_status', 'unknown'),
            'dataSource': payload.get('data_source', 'unknown'),
            'statusReason': payload.get('status_reason'),
            'isStale': bool(payload.get('is_stale', False)),
            'heartbeat_age_sec': payload.get('heartbeat_age_sec'),
            'last_activity_as_of': payload.get('last_activity_as_of'),
            'as_of': payload.get('as_of') or utc_now_iso(),
        }

    async def get_execution(self) -> dict:
        payload = self.repository.latest_snapshot()
        if payload is None:
            self._schedule_background_refresh()
            payload = self._mark_snapshot(None, data_status='no_data', data_source='empty', status_reason='snapshot_unavailable', is_stale=True)
        elif self._snapshot_is_stale(payload, self.SNAPSHOT_TTL_SECONDS):
            self._schedule_background_refresh()
            payload = self._mark_snapshot(payload, data_status='stale', data_source='cache', status_reason='stale_snapshot', is_stale=True)
        else:
            payload = self._mark_snapshot(payload, data_status='ok', data_source='cache', status_reason=None, is_stale=False)
        return {
            'status': payload.get('execution_status', 'unknown'),
            'execution': payload.get('execution', {}),
            'planner': payload.get('planner', {}),
            'execution_state': payload.get('execution_state', {}),
            'block_reasons': payload.get('block_reasons', []),
            'dataStatus': payload.get('data_status', 'unknown'),
            'dataSource': payload.get('data_source', 'unknown'),
            'statusReason': payload.get('status_reason'),
            'isStale': bool(payload.get('is_stale', False)),
            'as_of': payload.get('as_of') or utc_now_iso(),
        }

    async def get_services(self) -> dict:
        payload = self.repository.latest_snapshot()
        if payload is None:
            self._schedule_background_refresh()
            payload = self._mark_snapshot(None, data_status='no_data', data_source='empty', status_reason='snapshot_unavailable', is_stale=True)
        elif self._snapshot_is_stale(payload, self.SNAPSHOT_TTL_SECONDS):
            self._schedule_background_refresh()
            payload = self._mark_snapshot(payload, data_status='stale', data_source='cache', status_reason='stale_snapshot', is_stale=True)
        else:
            payload = self._mark_snapshot(payload, data_status='ok', data_source='cache', status_reason=None, is_stale=False)
        return {
            'items': self.repository.latest_service_statuses(),
            'dataStatus': payload.get('data_status', 'unknown'),
            'dataSource': payload.get('data_source', 'unknown'),
            'statusReason': payload.get('status_reason'),
            'isStale': bool(payload.get('is_stale', False)),
            'as_of': payload.get('as_of') or utc_now_iso(),
        }

    async def get_system_debug(self) -> dict:
        latest = self.repository.latest_snapshot()
        background_refresh_scheduled = False
        if latest is None:
            self._schedule_background_refresh()
            background_refresh_scheduled = True
            payload = self._mark_snapshot(None, data_status='no_data', data_source='empty', status_reason='snapshot_unavailable', is_stale=True)
            read_mode = 'empty_snapshot'
        elif self._snapshot_is_stale(latest, self.SNAPSHOT_TTL_SECONDS):
            self._schedule_background_refresh()
            background_refresh_scheduled = True
            payload = self._mark_snapshot(latest, data_status='stale', data_source='cache', status_reason='stale_snapshot', is_stale=True)
            read_mode = 'stale_cache_read'
        else:
            payload = self._mark_snapshot(latest, data_status='ok', data_source='cache', status_reason=None, is_stale=False)
            read_mode = 'fresh_cache_read'

        services = payload.get('services', {})
        block_reasons = payload.get('block_reasons', [])
        return {
            'scope': 'monitoring.system',
            'status': payload.get('data_status', 'unknown'),
            'source': payload.get('data_source', 'unknown'),
            'reason': payload.get('status_reason'),
            'as_of': payload.get('as_of') or utc_now_iso(),
            'timings': {
                'ttl_sec': self.SNAPSHOT_TTL_SECONDS,
                'snapshot_age_sec': self._snapshot_age_sec(payload),
                'data_freshness_sec': float(payload.get('data_freshness_sec', 0.0) or 0.0),
            },
            'summary': {
                'system_status': payload.get('system_status', 'unknown'),
                'execution_status': payload.get('execution_status', 'unknown'),
                'worker_status': payload.get('worker_status', 'unknown'),
                'queue': int(payload.get('queue', 0) or 0),
                'latency_ms': float(payload.get('latency_ms', 0.0) or 0.0),
                'exchange_latency_ms': float(payload.get('exchange_latency_ms', 0.0) or 0.0),
            },
            'provenance': {
                'read_mode': read_mode,
                'background_refresh_scheduled': background_refresh_scheduled,
                'snapshot_store': 'monitoring_snapshots',
                'service_status_store': 'service_status_snapshots',
                'upstream_dependencies': [
                    'v12:/system/health',
                    'v12:/execution/quality/latest',
                    'v12:/runtime/status',
                    'v12:/execution/planner/latest',
                    'v12:/execution/state/latest',
                    'v12:/execution/block-reasons/latest',
                    'v12:/strategy/risk-budget',
                    'v12:/risk/latest',
                ],
            },
            'counts': {
                'service_count': len(services) if isinstance(services, dict) else 0,
                'block_reason_count': len(block_reasons) if isinstance(block_reasons, list) else 0,
            },
            'raw': {
                'snapshot': payload,
                'services': self.repository.latest_service_statuses(),
            },
        }
