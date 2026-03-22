from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_command_center_realtime_websocket_stream() -> None:
    with client.websocket_connect('/api/v1/command-center/ws/events') as websocket:
        first = websocket.receive_json()
        assert first['event_type'] == 'hello'

        events = [websocket.receive_json() for _ in range(5)]
        event_types = {event['event_type'] for event in events}
        assert 'pnl_update' in event_types
        assert 'execution_event' in event_types
        assert 'risk_alert' in event_types
        assert 'strategy_status' in event_types
        assert 'system_status' in event_types


def test_command_center_realtime_includes_control_change() -> None:
    client.post('/api/v1/command-center/risk/pause', json={'note': 'ws-test'})

    with client.websocket_connect('/api/v1/command-center/ws/events') as websocket:
        websocket.receive_json()  # hello
        events = [websocket.receive_json() for _ in range(5)]
        risk_event = next(event for event in events if event['event_type'] == 'risk_alert')
        assert risk_event['payload']['trading_state'] == 'paused'
