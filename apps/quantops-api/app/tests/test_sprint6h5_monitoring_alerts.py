from datetime import datetime, timezone, timedelta

from app.services.monitoring_service import MonitoringService
from app.services.alert_service import AlertService


class DummyAlertRepo:
    def __init__(self):
        self.items = []
    def find_open_by_type(self, alert_type):
        return [x for x in self.items if x['alert_type'] == alert_type]
    def create_alert(self, payload):
        self.items.append(payload)
        return payload
    def list_alerts(self):
        return self.items
    def acknowledge(self, alert_id, status='acknowledged'):
        return {'alert_id': alert_id, 'status': status}


class DummyRiskRepo:
    def latest_snapshot(self):
        return {'trading_state': 'halted', 'alert_state': 'breach', 'drawdown': 0.2, 'gross_exposure': 1.1, 'risk_limit': {'margin_utilization': 0.95}}


class DummyMonitoringRepo:
    def latest_snapshot(self):
        return {'planner': {'expired_count': 2, 'plan_count': 12, 'route_mix': {'split_book': 3}}, 'worker_status': 'degraded'}


def test_sprint6h5_monitoring_worker_degraded_when_planner_active_without_execution() -> None:
    now = datetime.now(timezone.utc)
    service = MonitoringService.__new__(MonitoringService)
    status, last_as_of, age = service._worker_activity(
        {'latest_run_timestamp': (now - timedelta(seconds=5)).isoformat(), 'latest_execution_timestamp': (now - timedelta(seconds=120)).isoformat(), 'as_of': (now - timedelta(seconds=5)).isoformat()},
        {'as_of': (now - timedelta(seconds=120)).isoformat()},
        {'as_of': (now - timedelta(seconds=5)).isoformat()},
        {'as_of': (now - timedelta(seconds=2)).isoformat()},
    )
    assert status == 'degraded'
    assert last_as_of is not None
    assert age is not None


def test_sprint6h5_alerts_include_expiry_overflow_routing_and_blocked() -> None:
    repo = DummyAlertRepo()
    service = AlertService(repo, None, DummyRiskRepo(), DummyMonitoringRepo())
    result = service.evaluate_rules()
    types = {item['alert_type'] for item in result['created']}
    assert {'execution_blocked', 'plan_expired', 'planner_overflow', 'routing_fallback', 'margin_utilization_high'} <= types
