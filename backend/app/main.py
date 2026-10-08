from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.routers.state import router as state_router
from app.services.ticketing import TicketingService
from app.websocket.manager import ConnectionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.connections = ConnectionManager()
    app.state.ticketing = TicketingService(app.state.connections.broadcast_state)
    yield


app = FastAPI(
    title="Sistema de Atención al Cliente",
    description="API de turnos con cuatro mesas y sincronización WebSocket.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(state_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    manager: ConnectionManager = websocket.app.state.connections
    await manager.connect(websocket)
    try:
        await websocket.send_json(
            websocket.app.state.ticketing.snapshot().model_dump(mode="json")
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
