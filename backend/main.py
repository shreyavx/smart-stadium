
import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.auth.config import (
    get_auth_settings,
    get_trusted_origins,
    is_trusted_origin,
)
from backend.auth.dependencies import authenticate_websocket, require_roles
from backend.auth.router import router as auth_router
from backend.friends.database import initialize_database
from backend.simulator.engine import CrowdSimulator
from backend.api.connection_manager import ConnectionManager

from backend.intelligence.congestion import CongestionDetector
from backend.intelligence.forecast import CrowdForecaster
from backend.intelligence.alerts import AlertGenerator
from backend.api.friends import router as friends_router


# Shared application objects
simulator = CrowdSimulator()
manager = ConnectionManager()

congestion_detector = CongestionDetector()
crowd_forecaster = CrowdForecaster()
alert_generator = AlertGenerator()

simulation_task = None

# Initial data for newly connected clients
latest_update = {
    "event": "stadium_update",
    "data": simulator.get_snapshot(),
    "congestion": {},
    "forecasts": {},
    "alerts": []
}


async def simulation_loop():
    """Update stadium data and broadcast intelligence every 2 seconds."""

    global latest_update

    while True:
        # 1. Simulate crowd movement
        snapshot = simulator.step()

        # 2. Detect current congestion
        congestion = congestion_detector.analyze(snapshot)

        # 3. Forecast occupancy 5 minutes ahead
        forecasts = crowd_forecaster.forecast(snapshot)

        # 4. Generate operator alerts
        alerts = alert_generator.generate(
            congestion,
            forecasts
        )

        # 5. Combine all results
        latest_update = {
            "event": "stadium_update",
            "data": snapshot,
            "congestion": congestion,
            "forecasts": forecasts,
            "alerts": alerts
        }

        # 6. Broadcast to connected clients
        await manager.broadcast(latest_update)

        await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global simulation_task

    initialize_database()
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

app.include_router(friends_router)
app.include_router(auth_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_trusted_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-User-ID"],
)


@app.middleware("http")
async def validate_cookie_request_origin(request: Request, call_next):
    settings = get_auth_settings()
    if (
        request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and request.cookies.get(settings.cookie_name)
        and not is_trusted_origin(request.headers.get("origin"))
    ):
        return JSONResponse(
            status_code=403,
            content={"detail": "Untrusted request origin."},
        )
    return await call_next(request)


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


@app.get(
    "/stadium/snapshot",
    dependencies=[Depends(require_roles("USER", "CONTROLLER"))],
)
def get_snapshot():
    return simulator.get_snapshot()


@app.post(
    "/simulate/surge",
    dependencies=[Depends(require_roles("CONTROLLER"))],
)
def trigger_surge(
    request: SurgeRequest,
):
    simulator.trigger_surge(
        request.zone_id,
        request.people_per_tick
    )

    return {
        "message": "Crowd surge activated",
        "zone_id": request.zone_id,
        "people_per_tick": request.people_per_tick
    }


@app.post(
    "/simulate/stop",
    dependencies=[Depends(require_roles("CONTROLLER"))],
)
def stop_surge():
    simulator.stop_surge()

    return {
        "message": "Crowd surge stopped"
    }


@app.websocket("/ws/stadium")
async def stadium_websocket(websocket: WebSocket):

    principal = await authenticate_websocket(
        websocket,
        ("USER", "CONTROLLER"),
    )
    if principal is None:
        return

    await manager.connect(websocket)

    try:
        # Send the latest complete update immediately.
        await websocket.send_json(latest_update)

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
