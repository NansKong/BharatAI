"""
WebSocket connection manager for real-time notification push.
Maintains an in-memory registry of connected clients per user_id.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Thread-safe (within single ASGI process) per-user WebSocket registry."""

    def __init__(self):
        # user_id (str) → list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(user_id, []).append(ws)
        logger.debug(
            "WS connected user=%s total=%d", user_id, len(self._connections[user_id])
        )

    def disconnect(self, user_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(user_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(user_id, None)
        logger.debug("WS disconnected user=%s", user_id)

    async def send_to_user(self, user_id: str, payload: dict[str, Any]) -> int:
        """Broadcast payload to all open connections for user_id. Returns count sent."""
        conns = list(self._connections.get(str(user_id), []))
        sent = 0
        for ws in conns:
            try:
                await ws.send_text(json.dumps(payload))
                sent += 1
            except Exception:
                self.disconnect(str(user_id), ws)
        return sent


# Global singleton — shared across all requests in one worker process
manager = ConnectionManager()
