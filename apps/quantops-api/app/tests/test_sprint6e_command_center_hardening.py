from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_command_center_hardening_status_and_rbac() -> None:
    status = client.get('/api/v1/command-center/hardening/status')
    assert status.status_code == 200
    body = status.json()
    assert body['rbac_enabled'] is True
    assert body['audit_enabled'] is True

    denied = client.post('/api/v1/command-center/strategies/start', json={'strategy_id': 's1'}, headers={'X-User-Role': 'viewer', 'X-User-Id': 'guest'})
    assert denied.status_code == 403

    allowed = client.post(
        '/api/v1/command-center/strategies/start',
        json={'strategy_id': 's1'},
        headers={'X-User-Role': 'operator', 'X-User-Id': 'alice'},
    )
    assert allowed.status_code == 200
    assert allowed.json()['ok'] is True


def test_command_center_audit_summary_and_notifications() -> None:
    client.post(
        '/api/v1/command-center/risk/pause',
        json={'note': 'rbac hardening'},
        headers={'X-User-Role': 'risk_manager', 'X-User-Id': 'risk-bot'},
    )
    denied = client.get('/api/v1/command-center/audit/summary', headers={'X-User-Role': 'viewer', 'X-User-Id': 'guest'})
    assert denied.status_code == 403

    audit = client.get(
        '/api/v1/command-center/audit/summary',
        headers={'X-User-Role': 'admin', 'X-User-Id': 'root'},
    )
    assert audit.status_code == 200
    body = audit.json()
    assert len(body['operator_actions']) >= 1
    assert any(item['event_type'] == 'risk_alert_notify' for item in body['audit_logs'])
