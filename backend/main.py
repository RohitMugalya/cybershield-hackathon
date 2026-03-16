"""
CyberShield - FastAPI Backend
REST API + WebSocket for real-time communication
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import json
import asyncio
import random
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.simulated_data import (
    CAMERAS, AREAS, POLICE_OFFICERS,
    generate_incidents, generate_vehicle_detections,
    search_vehicle_by_plate, search_vehicles_by_characteristics,
    get_system_metrics,
)

app = FastAPI(
    title="CyberShield API",
    description="AI-Based Integrated Video Analytics System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── WebSocket Connection Manager ─────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, area_id: str):
        await websocket.accept()
        if area_id not in self.active_connections:
            self.active_connections[area_id] = []
        self.active_connections[area_id].append(websocket)

    def disconnect(self, websocket: WebSocket, area_id: str):
        if area_id in self.active_connections:
            self.active_connections[area_id].remove(websocket)

    async def broadcast_to_area(self, area_id: str, message: dict):
        if area_id in self.active_connections:
            dead = []
            for ws in self.active_connections[area_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active_connections[area_id].remove(ws)

    async def broadcast_all(self, message: dict):
        for area_id in self.active_connections:
            await self.broadcast_to_area(area_id, message)


manager = ConnectionManager()


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"message": "CyberShield API is running", "version": "1.0.0", "status": "healthy"}


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {"api": "up", "db": "simulated", "redis": "simulated"},
    }


# ─── Metrics ──────────────────────────────────────────────────────────────────
@app.get("/api/metrics", tags=["Analytics"])
def get_metrics():
    return get_system_metrics()


@app.get("/api/cameras", tags=["Cameras"])
def get_cameras():
    return CAMERAS


@app.get("/api/cameras/{camera_id}", tags=["Cameras"])
def get_camera(camera_id: int):
    cam = next((c for c in CAMERAS if c["camera_id"] == camera_id), None)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam


@app.get("/api/areas", tags=["Areas"])
def get_areas():
    return AREAS


# ─── Incidents ────────────────────────────────────────────────────────────────
@app.get("/api/incidents", tags=["Incidents"])
def get_incidents(area_id: Optional[int] = None, limit: int = 20):
    incidents = generate_incidents(limit)
    if area_id:
        incidents = [i for i in incidents if i.get("area_id") == area_id]
    # Convert datetime to string for JSON
    for inc in incidents:
        if "created_at" in inc:
            inc["created_at"] = inc["created_at"].isoformat()
    return incidents


@app.post("/api/incidents/{incident_id}/respond", tags=["Incidents"])
def mark_responded(incident_id: int, officer_id: int):
    return {
        "success": True,
        "message": f"Incident #{incident_id} marked as responded by Officer #{officer_id}",
        "timestamp": datetime.now().isoformat(),
    }


# ─── Vehicle Search ───────────────────────────────────────────────────────────
@app.get("/api/vehicles/search", tags=["Vehicles"])
def search_vehicle(plate: Optional[str] = None, vehicle_type: Optional[str] = None,
                   color: Optional[str] = None, area_id: Optional[int] = None):
    if plate:
        result = search_vehicle_by_plate(plate)
        if not result:
            raise HTTPException(status_code=404, detail=f"Vehicle {plate} not found")
        # Convert datetimes
        for det in result.get("recent_detections", []):
            if "detected_at" in det and hasattr(det["detected_at"], "isoformat"):
                det["detected_at"] = det["detected_at"].isoformat()
        return result
    elif vehicle_type or color:
        results = search_vehicles_by_characteristics(vehicle_type, color, area_id)
        for r in results:
            if "last_seen_time" in r and hasattr(r["last_seen_time"], "isoformat"):
                r["last_seen_time"] = r["last_seen_time"].isoformat()
        return results
    else:
        raise HTTPException(status_code=400, detail="Provide plate or vehicle_type/color")


# ─── Police Officers ──────────────────────────────────────────────────────────
@app.get("/api/officers", tags=["Officers"])
def get_officers(area_id: Optional[int] = None):
    officers = POLICE_OFFICERS
    if area_id:
        officers = [o for o in officers if o.get("area_id") == area_id]
    return officers


@app.post("/api/auth/officer-login", tags=["Auth"])
def officer_login(badge_id: str, password: str):
    if password != "officer@123":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    officer = next((o for o in POLICE_OFFICERS if o["badge"] == badge_id), None)
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")
    return {"success": True, "officer": officer, "token": "simulated-jwt-token"}


# ─── WebSocket: Real-time Alerts ──────────────────────────────────────────────
@app.websocket("/ws/alerts/{area_id}")
async def websocket_alerts(websocket: WebSocket, area_id: str):
    await manager.connect(websocket, area_id)
    try:
        while True:
            # Listen for client messages
            data = await asyncio.wait_for(websocket.receive_text(), timeout=15)
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
    except asyncio.TimeoutError:
        # Send heartbeat
        try:
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "active_alerts": random.randint(0, 3),
            })
        except Exception:
            pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, area_id)
    except Exception:
        manager.disconnect(websocket, area_id)


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            metrics = get_system_metrics()
            metrics["timestamp"] = datetime.now().isoformat()
            await websocket.send_json(metrics)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
