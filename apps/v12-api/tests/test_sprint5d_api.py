from fastapi.testclient import TestClient

from ai_hedge_bot.api.app import app


client = TestClient(app)


def test_sprint5d_modes_and_acceptance_flow():
    modes = client.get('/runtime/modes')
    assert modes.status_code == 200
    assert any(x['mode'] == 'paper' for x in modes.json()['modes'])

    set_mode = client.post('/runtime/modes/set', json={'mode': 'shadow'})
    assert set_mode.status_code == 200
    assert set_mode.json()['runtime_mode'] == 'shadow'

    run_resp = client.post('/runtime/run-with-mode', json={
        'run_id': 'test_s5d_shadow_001',
        'mode': 'shadow',
        'expected_pnl': 120.0,
        'order_count': 4,
        'slippage_drag': 5.0,
        'fee_drag': 2.0,
        'latency_drag': 1.0,
    })
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body['runtime_mode'] == 'shadow'
    assert body['status'] == 'ok'

    shadow = client.get('/analytics/shadow-summary')
    assert shadow.status_code == 200
    assert shadow.json()['run_id'] == 'test_s5d_shadow_001'

    acceptance = client.get('/acceptance/status', params={'run_id': 'test_s5d_shadow_001'})
    assert acceptance.status_code == 200
    assert acceptance.json()['passed'] is True


def test_sprint5d_live_ready_block_creates_incident():
    run_resp = client.post('/runtime/run-with-mode', json={
        'run_id': 'test_s5d_live_ready_001',
        'mode': 'live_ready',
        'has_live_credentials': False,
        'hard_risk_pass': False,
    })
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body['status'] == 'blocked'
    assert body['runtime_mode'] == 'live_ready'

    incidents = client.get('/incidents/latest')
    assert incidents.status_code == 200
    payload = incidents.json()['incidents']
    assert any(item['run_id'] == 'test_s5d_live_ready_001' for item in payload)

    checks = client.get('/acceptance/checks', params={'run_id': 'test_s5d_live_ready_001'})
    assert checks.status_code == 200
    assert any(item['passed'] is False for item in checks.json()['checks'])
