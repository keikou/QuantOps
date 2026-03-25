import json
from datetime import datetime, timezone

from app.clients.v12_client import utc_now_iso


class AlertService:
    ALERTS_CACHE_TTL_SECONDS = 5.0

    def __init__(self, repository, audit_repository, risk_repository, monitoring_repository=None):
        self.repository = repository
        self.audit_repository = audit_repository
        self.risk_repository = risk_repository
        self.monitoring_repository = monitoring_repository
        self._alerts_cache = None

    @staticmethod
    def _snapshot_age_sec(value):
        if not value:
            return None
        try:
            ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            return max(0.0, (datetime.now(timezone.utc) - ts).total_seconds())
        except Exception:
            return None

    def _create_once(self, payload: dict, created: list) -> None:
        existing = self.repository.find_open_by_type(payload['alert_type'])
        if not existing:
            created.append(self.repository.create_alert(payload))

    def evaluate_rules(self) -> dict:

        latest = self.risk_repository.latest_snapshot()
        monitoring = self.monitoring_repository.latest_snapshot() if self.monitoring_repository else None
        planner = (monitoring or {}).get('planner', {}) if monitoring else {}
        execution_state = (monitoring or {}).get('execution_state', {}) if monitoring else {}
        block_reasons = (monitoring or {}).get('block_reasons', []) if monitoring else []

        created = []

        if latest and str(latest.get('trading_state', 'running') or 'running').lower() == 'halted':
            self._create_once(
                {
                    'alert_type': 'trading_halted',
                    'severity': 'critical',
                    'source_service': 'risk',
                    'source': 'risk_control_state',
                    'title': 'Trading halted by risk system',
                    'message': json.dumps({'trading_state': latest.get('trading_state'), 'kill_switch': latest.get('kill_switch')}),
                    'status': 'open',
                    'payload': latest,
                },
                created,
            )
            self._create_once(
                {
                    'alert_type': 'execution_blocked',
                    'severity': 'critical',
                    'source_service': 'scheduler',
                    'source': 'runtime_control_state',
                    'title': 'Execution blocked by trading state',
                    'message': json.dumps({'trading_state': latest.get('trading_state')}),
                    'status': 'open',
                    'payload': latest,
                },
                created,
            )

        if latest and latest.get('alert_state') == 'breach':
            self._create_once(
                {
                    'alert_type': 'drawdown_breach',
                    'severity': 'high',
                    'source_service': 'risk',
                    'source': 'risk_snapshot',
                    'title': 'Risk threshold breached',
                    'message': json.dumps({'drawdown': latest.get('drawdown'), 'gross_exposure': latest.get('gross_exposure')}),
                    'status': 'open',
                    'payload': latest,
                },
                created,
            )

        margin_utilization = float((((latest or {}).get('risk_limit') or {}).get('margin_utilization', 0.0)) or 0.0)
        if margin_utilization >= 0.9:
            self._create_once(
                {
                    'alert_type': 'margin_utilization_high',
                    'severity': 'high',
                    'source_service': 'risk',
                    'source': 'risk_limit',
                    'title': 'Margin utilization high',
                    'message': json.dumps({'margin_utilization': margin_utilization}),
                    'status': 'open',
                    'payload': latest or {},
                },
                created,
            )

        if planner:
            if int(planner.get('expired_count', 0) or 0) > 0:
                self._create_once(
                    {
                        'alert_type': 'plan_expired',
                        'severity': 'medium',
                        'source_service': 'planner',
                        'source': 'execution_planner',
                        'title': 'Execution plans expired',
                        'message': json.dumps({'expired_count': planner.get('expired_count')}),
                        'status': 'open',
                        'payload': planner,
                    },
                    created,
                )
            if int(planner.get('plan_count', 0) or 0) >= 10:
                self._create_once(
                    {
                        'alert_type': 'planner_overflow',
                        'severity': 'high',
                        'source_service': 'planner',
                        'source': 'execution_planner',
                        'title': 'Planner queue is building up',
                        'message': json.dumps({'plan_count': planner.get('plan_count')}),
                        'status': 'open',
                        'payload': planner,
                    },
                    created,
                )
            routes = planner.get('route_mix') or {}
            if any('taker' in str(k) or 'split' in str(k) for k in routes.keys()):
                self._create_once(
                    {
                        'alert_type': 'routing_fallback',
                        'severity': 'medium',
                        'source_service': 'planner',
                        'source': 'execution_planner',
                        'title': 'Routing fallback used',
                        'message': json.dumps({'route_mix': routes}),
                        'status': 'open',
                        'payload': planner,
                    },
                    created,
                )
        if execution_state:
            execution_status = str(execution_state.get('execution_state', '') or '')
            reason = str(execution_state.get('reason') or '')
            open_order_count = int(execution_state.get('open_order_count', 0) or 0)
            if execution_status in {'blocked', 'halted'}:
                self._create_once(
                    {
                        'alert_type': 'execution_blocked',
                        'severity': 'critical' if execution_status == 'halted' else 'high',
                        'source_service': 'execution',
                        'source': 'execution_state',
                        'title': 'Execution is blocked',
                        'message': json.dumps({'execution_state': execution_status, 'reason': execution_state.get('reason')}),
                        'status': 'open',
                        'payload': execution_state,
                    },
                    created,
                )
            if execution_status == 'degraded':
                self._create_once(
                    {
                        'alert_type': 'no_recent_execution',
                        'severity': 'medium',
                        'source_service': 'execution',
                        'source': 'execution_state',
                        'title': 'Execution is degraded',
                        'message': json.dumps({'execution_state': execution_status, 'planner_age_sec': execution_state.get('planner_age_sec'), 'execution_age_sec': execution_state.get('execution_age_sec'), 'reason': reason}),
                        'status': 'open',
                        'payload': execution_state,
                    },
                    created,
                )
            if any(str(item.get('code')) == 'stale_open_orders' for item in block_reasons) or reason == 'stale_open_orders':
                self._create_once(
                    {
                        'alert_type': 'stale_open_orders',
                        'severity': 'high',
                        'source_service': 'execution',
                        'source': 'execution_state',
                        'title': 'Open orders are stale',
                        'message': json.dumps({'open_order_count': open_order_count, 'reason': reason}),
                        'status': 'open',
                        'payload': execution_state,
                    },
                    created,
                )
            if open_order_count >= 25 and (str((latest or {}).get('trading_state', 'running')).lower() == 'halted' or reason in {'expired_plan', 'stale_open_orders', 'residual_orders_after_halt', 'open_orders_not_draining'}):
                self._create_once(
                    {
                        'alert_type': 'execution_order_accumulation',
                        'severity': 'critical',
                        'source_service': 'execution',
                        'source': 'execution_state',
                        'title': 'Open orders are accumulating in a blocked or stale state',
                        'message': json.dumps({'open_order_count': open_order_count, 'reason': reason, 'trading_state': (latest or {}).get('trading_state')}),
                        'status': 'open',
                        'payload': execution_state,
                    },
                    created,
                )
        if any(str(item.get('code')) == 'no_fill_after_submit' for item in block_reasons):
            self._create_once(
                {
                    'alert_type': 'no_fill_after_submit',
                    'severity': 'high',
                    'source_service': 'execution',
                    'source': 'execution_block_reasons',
                    'title': 'Orders submitted without fills',
                    'message': json.dumps({'reasons': block_reasons}),
                    'status': 'open',
                    'payload': {'items': block_reasons},
                },
                created,
            )

        return {'ok': True, 'created': created}

    def list_alerts(self):
        cached = self._alerts_cache
        cache_age = self._snapshot_age_sec((cached or {}).get("_cached_at")) if isinstance(cached, dict) else None
        if cache_age is not None and cache_age <= self.ALERTS_CACHE_TTL_SECONDS:
            result = dict(cached)
            result["build_status"] = "fresh_cache"
            result.pop("_cached_at", None)
            return result

        items = self.repository.list_alerts()
        open_items = [item for item in items if str(item.get('status', 'open') or 'open').lower() == 'open']
        critical_open = [item for item in open_items if str(item.get('severity', '') or '').lower() == 'critical']
        payload = {
            'count': len(open_items),
            'open_count': len(open_items),
            'total_count': len(items),
            'critical_count': len(critical_open),
            'items': items,
            'as_of': utc_now_iso(),
            'build_status': 'live',
        }
        self._alerts_cache = {**payload, "_cached_at": utc_now_iso()}
        return payload

    def acknowledge(self, alert_id: str):
        return self.repository.acknowledge(alert_id)
