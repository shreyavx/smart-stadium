
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.simulator.engine import CrowdSimulator
from backend.api.connection_manager import ConnectionManager

from backend.intelligence.congestion import CongestionDetector
from backend.intelligence.forecast import CrowdForecaster
from backend.intelligence.alerts import AlertGenerator
from backend.intelligence.routing import find_dynamic_route
from backend.api.friends import router as friends_router
from backend.friends.database import initialize_database


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
    "alerts": [],
    "blocked_connections": [],
    "evacuation": {
        "active": False,
        "destination": None
    }
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
            "alerts": alerts,
            "blocked_connections": [
                {"source": u, "destination": v}
                for u, v in sorted(blocked_connections)
            ],
            "evacuation": {
                "active": getattr(simulator, "evacuation_mode", False),
                "destination": getattr(simulator, "evacuation_destination", None)
            }
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SurgeRequest(BaseModel):
    zone_id: str
    people_per_tick: int = 30


class RouteRequest(BaseModel):
    start_zone: str
    destination_zone: str


class BlockConnectionRequest(BaseModel):
    source: str
    destination: str


class EvacuationRequest(BaseModel):
    destination: str = "CENTRAL_EXIT"


# Set of currently blocked connection tuples: (u, v)
blocked_connections = set()


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


@app.post("/simulate/evacuate/start")
def start_evacuation(request: EvacuationRequest):
    try:
        simulator.start_evacuation(request.destination)
        return {
            "message": "Emergency Evacuation Simulation activated",
            "destination": request.destination,
            "evacuation_mode": True
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/simulate/evacuate/stop")
def stop_evacuation():
    simulator.stop_evacuation()
    return {
        "message": "Emergency Evacuation Simulation deactivated",
        "evacuation_mode": False
    }


@app.post("/route")
def get_route(request: RouteRequest):
    try:
        current_snapshot = simulator.get_snapshot()
        result = find_dynamic_route(
            start_zone=request.start_zone,
            destination_zone=request.destination_zone,
            snapshot_data=current_snapshot,
            closed_connections=list(blocked_connections)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/route")
def get_route_query(start_zone: str, destination_zone: str):
    try:
        current_snapshot = simulator.get_snapshot()
        result = find_dynamic_route(
            start_zone=start_zone,
            destination_zone=destination_zone,
            snapshot_data=current_snapshot,
            closed_connections=list(blocked_connections)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/connections/blocked")
def get_blocked_connections():
    return {
        "blocked_connections": [
            {"source": u, "destination": v}
            for u, v in sorted(blocked_connections)
        ]
    }


@app.post("/connections/block")
def block_connection(request: BlockConnectionRequest):
    pair = tuple(sorted([request.source, request.destination]))
    blocked_connections.add(pair)
    return {
        "message": f"Connection {pair[0]} <-> {pair[1]} is now BLOCKED.",
        "blocked_connection": {"source": pair[0], "destination": pair[1]},
        "total_blocked": len(blocked_connections)
    }


@app.post("/connections/reopen")
def reopen_connection(request: BlockConnectionRequest):
    pair = tuple(sorted([request.source, request.destination]))
    if pair in blocked_connections:
        blocked_connections.remove(pair)
        return {
            "message": f"Connection {pair[0]} <-> {pair[1]} has been REOPENED.",
            "reopened_connection": {"source": pair[0], "destination": pair[1]},
            "total_blocked": len(blocked_connections)
        }
    return {
        "message": f"Connection {pair[0]} <-> {pair[1]} was not blocked.",
        "total_blocked": len(blocked_connections)
    }


@app.websocket("/ws/stadium")
async def stadium_websocket(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        # Send the latest complete update immediately.
        await websocket.send_json(latest_update)

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
