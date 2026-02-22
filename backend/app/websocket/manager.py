from collections import defaultdict, deque
import asyncio
import json
import logging
from typing import Any, Deque, Dict, List, Optional, Set

from fastapi import WebSocket

from ..core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.connection_municipality: Dict[WebSocket, str] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._events: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=settings.WS_EVENT_REPLAY_LIMIT)
        )

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, websocket: WebSocket, municipality_id: str):
        await websocket.accept()

        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        self.active_connections[municipality_id].add(websocket)
        self.connection_municipality[websocket] = municipality_id
        logger.info("WebSocket connected for municipality=%s", municipality_id)

    def disconnect(self, websocket: WebSocket):
        municipality_id = self.connection_municipality.get(websocket)
        if municipality_id:
            self.active_connections[municipality_id].discard(websocket)
            if not self.active_connections[municipality_id]:
                del self.active_connections[municipality_id]

        if websocket in self.connection_municipality:
            del self.connection_municipality[websocket]

        logger.info("WebSocket disconnected for municipality=%s", municipality_id)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as exc:
            logger.error("Error sending personal WS message: %s", exc)

    async def broadcast_to_municipality(self, municipality_id: str, message: Dict[str, Any]):
        connections = list(self.active_connections.get(municipality_id, set()))
        if not connections:
            return

        disconnected = []
        payload = json.dumps(message)
        for connection in connections:
            try:
                await connection.send_text(payload)
            except Exception as exc:
                logger.warning("WS broadcast failed for municipality=%s: %s", municipality_id, exc)
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_all(self, message: Dict[str, Any]):
        for municipality_id in list(self.active_connections.keys()):
            await self.broadcast_to_municipality(municipality_id, message)

    def _thread_safe_broadcast(self, municipality_id: str, message: Dict[str, Any]):
        if not self._loop or not self._loop.is_running():
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.broadcast_to_municipality(municipality_id, message),
                self._loop,
            )
        except Exception as exc:
            logger.error("Error scheduling WS broadcast: %s", exc)

    def add_event(self, municipality_id: str, event: Dict[str, Any]):
        self._events[municipality_id].appendleft(event)
        # National/global replay feed for super admin clients.
        self._events["global"].appendleft(event)

    def get_events(self, municipality_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        return list(self._events.get(municipality_id, deque()))[:limit]

    def broadcast_sensor_reading(self, municipality_id: str, data: Dict[str, Any]):
        event = {"type": "sensor_reading", "data": data}
        self._thread_safe_broadcast(municipality_id, event)

    def broadcast_alert(self, municipality_id: str, alert_data: Dict[str, Any]):
        event = {"type": "alert", "data": alert_data}
        self._thread_safe_broadcast(municipality_id, event)
        self.add_event(municipality_id, {"event_type": "alert", **alert_data})

    def broadcast_incident(self, municipality_id: str, incident_data: Dict[str, Any]):
        event = {"type": "incident", "data": incident_data}
        self._thread_safe_broadcast(municipality_id, event)
        self.add_event(municipality_id, {"event_type": "incident", **incident_data})

    def broadcast_system_update(self, data: Dict[str, Any]):
        if not self._loop or not self._loop.is_running():
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.broadcast_all({"type": "system_update", "data": data}),
                self._loop,
            )
        except Exception as exc:
            logger.error("Error broadcasting system update: %s", exc)


ws_manager = ConnectionManager()
