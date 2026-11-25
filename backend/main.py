from fastapi.middleware.cors import CORSMiddleware

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.simulator.engine import CrowdSimulator
from backend.api.connection_manager import ConnectionManager


# Shared application objects
simulator = CrowdSimulator()
manager = ConnectionManager()

simulation_task = None


async def simulation_loop():
    """Continuously update and broadcast stadium data."""

    while True:
        snapshot = simulator.step()

        await manager.broadcast({
            "event": "stadium_update",
            "data": snapshot
        })

        await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global simulation_task

    simulation_task = asyncio.create_task(simulation_loop())

    yield

    simulation_task.cancel()

    try:
        await simulation_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="SmartStadium API",
    description="Real-time Stadium Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SurgeRequest(BaseModel):
    zone_id: str
    people_per_tick: int = 30


@app.get("/")
def home():
    return {
        "project": "SmartStadium",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "backend"
    }


@app.get("/stadium/snapshot")
def get_snapshot():
    return simulator.get_snapshot()


@app.post("/simulate/surge")
def trigger_surge(request: SurgeRequest):
    simulator.trigger_surge(
        request.zone_id,
        request.people_per_tick
    )

    return {
        "message": "Crowd surge activated",
        "zone_id": request.zone_id,
        "people_per_tick": request.people_per_tick
    }


@app.post("/simulate/stop")
def stop_surge():
    simulator.stop_surge()

    return {
        "message": "Crowd surge stopped"
    }


@app.websocket("/ws/stadium")
async def stadium_websocket(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        # Immediately send the current state.
        await websocket.send_json({
            "event": "stadium_update",
            "data": simulator.get_snapshot()
        })

        while True:
            # Keep connection alive and detect disconnections.
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
