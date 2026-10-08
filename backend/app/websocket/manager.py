from fastapi import WebSocket

from app.models.state import SystemState


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast_state(self, state: SystemState) -> None:
        stale_connections: list[WebSocket] = []
        for connection in tuple(self._connections):
            try:
                await connection.send_json(state.model_dump(mode="json"))
            except Exception:
                stale_connections.append(connection)
        for connection in stale_connections:
            self.disconnect(connection)
