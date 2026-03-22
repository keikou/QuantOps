from app.services.alert_service import AlertService


class Repo:
    def __init__(self):
        self.created = []
    def find_open_by_type(self, alert_type):
        return None
    def create_alert(self, payload):
        self.created.append(payload)
        return payload
    def list_alerts(self):
        return self.created


class AuditRepo:
    pass


class RiskRepo:
    def latest_snapshot(self):
        return {'trading_state': 'halted', 'kill_switch': 'triggered', 'alert_state': 'breach', 'drawdown': 0.2, 'gross_exposure': 1.1}


def test_halt_alert_is_created() -> None:
    repo = Repo()
    service = AlertService(repo, AuditRepo(), RiskRepo())
    payload = service.evaluate_rules()
    assert payload['ok'] is True
    types = {item['alert_type'] for item in repo.created}
    assert 'trading_halted' in types
