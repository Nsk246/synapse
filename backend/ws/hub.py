"""
Synapse WebSocket Connection Manager.

Maintains the set of active WebSocket connections and provides
a broadcast method to push events to all connected clients.

Thread-safe for FastAPI's async event loop.
"""
from __future__ import annotations
import json
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)
        print(f"▸ WS client connected  (total: {len(self.active)})")

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)
        print(f"▸ WS client disconnected (total: {len(self.active)})")

    async def broadcast(self, payload: dict) -> None:
        """Send a JSON payload to every connected client."""
        message = json.dumps(payload)
        disconnected: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)


# Module-level singleton — imported by main.py and events.py
manager = ConnectionManager()
