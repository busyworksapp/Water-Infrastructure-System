import sys

sys.path.insert(0, "backend")

from app.core.security import create_access_token, decode_token
from app.websocket.manager import ConnectionManager


def test_access_token_round_trip():
    token = create_access_token({"sub": "user-123"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_websocket_event_replay_buffer():
    manager = ConnectionManager()
    manager.add_event("municipality-1", {"event_type": "sensor_reading", "reading_id": "r-1"})
    manager.add_event("municipality-1", {"event_type": "alert", "alert_id": "a-1"})

    events = manager.get_events("municipality-1", limit=10)
    assert len(events) == 2
    assert events[0]["event_type"] == "alert"
    assert events[1]["event_type"] == "sensor_reading"
