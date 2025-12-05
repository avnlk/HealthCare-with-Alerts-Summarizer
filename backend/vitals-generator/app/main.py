import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.vitals import vitals_generator, Patient
from app.elasticsearch_client import es_client

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Background task for continuous vitals update
async def vitals_update_task():
    """Background task to continuously update vitals."""
    while True:
        try:
            patients = vitals_generator.update_all_vitals()
            # Log to Elasticsearch
            patient_dicts = [p.model_dump() for p in patients]
            es_client.bulk_log_vitals(patient_dicts)
        except Exception as e:
            logger.error(f"Error updating vitals: {e}")
        
        await asyncio.sleep(settings.vitals_interval_ms / 1000)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    # Start background vitals update task
    task = asyncio.create_task(vitals_update_task())
    
    yield
    
    # Cleanup
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    logger.info("Shutting down vitals generator")


# Create FastAPI app
app = FastAPI(
    title="Vitals Generator Service",
    description="Generates and streams realistic medical vitals for simulated patients",
    version=settings.service_version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Store active WebSocket connections
active_connections: dict[str, list[WebSocket]] = {}


def patient_to_response(patient: Patient) -> dict:
    """Convert patient model to API response format."""
    return {
        "id": patient.id,
        "name": patient.name,
        "bedNumber": patient.bed_number,
        "age": patient.age,
        "gender": patient.gender,
        "admissionDate": patient.admission_date,
        "diagnosis": patient.diagnosis,
        "attendingPhysician": patient.attending_physician,
        "vitals": {
            "heartRate": patient.vitals.heart_rate,
            "spO2": patient.vitals.spo2,
            "bloodPressure": patient.vitals.blood_pressure,
            "temperature": patient.vitals.temperature,
            "respiratory": patient.vitals.respiratory_rate
        },
        "alertSeverity": patient.alert_severity
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version,
        "elasticsearch": es_client.health_check(),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/patients", response_model=None)
async def get_patients() -> List[dict]:
    """Get all patients with current vitals."""
    patients = vitals_generator.get_all_patients()
    return [patient_to_response(p) for p in patients]


@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    """Get a specific patient by ID."""
    patient = vitals_generator.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return patient_to_response(patient)


@app.get("/api/patients/{patient_id}/vitals")
async def get_patient_vitals(patient_id: str):
    """Get current vitals for a specific patient."""
    patient = vitals_generator.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return {
        "heartRate": patient.vitals.heart_rate,
        "spO2": patient.vitals.spo2,
        "bloodPressure": patient.vitals.blood_pressure,
        "temperature": patient.vitals.temperature,
        "respiratory": patient.vitals.respiratory_rate,
        "timestamp": patient.vitals.timestamp
    }


@app.get("/api/patients/{patient_id}/vitals/history")
async def get_vitals_history(patient_id: str, hours: int = Query(default=1, ge=1, le=24)):
    """Get historical vitals for a patient."""
    history = vitals_generator.get_patient_vitals_history(patient_id, hours)
    if not history:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    
    return {
        "heartRate": [{"timestamp": v.timestamp, "value": v.heart_rate} for v in history],
        "spO2": [{"timestamp": v.timestamp, "value": v.spo2} for v in history],
        "systolic": [{"timestamp": v.timestamp, "value": v.blood_pressure["systolic"]} for v in history],
        "diastolic": [{"timestamp": v.timestamp, "value": v.blood_pressure["diastolic"]} for v in history],
        "temperature": [{"timestamp": v.timestamp, "value": v.temperature} for v in history],
        "respiratory": [{"timestamp": v.timestamp, "value": v.respiratory_rate} for v in history]
    }


@app.websocket("/ws/vitals/{patient_id}")
async def websocket_vitals(websocket: WebSocket, patient_id: str):
    """WebSocket endpoint for real-time vitals streaming."""
    patient = vitals_generator.get_patient(patient_id)
    if not patient:
        await websocket.close(code=4004, reason="Patient not found")
        return
    
    await websocket.accept()
    
    # Add to active connections
    if patient_id not in active_connections:
        active_connections[patient_id] = []
    active_connections[patient_id].append(websocket)
    
    logger.info(f"WebSocket connected for patient {patient_id}")
    
    try:
        while True:
            # Update and send vitals
            patient = vitals_generator.update_vitals(patient_id)
            if patient:
                vitals_data = {
                    "heartRate": patient.vitals.heart_rate,
                    "spO2": patient.vitals.spo2,
                    "systolic": patient.vitals.blood_pressure["systolic"],
                    "diastolic": patient.vitals.blood_pressure["diastolic"],
                    "temperature": patient.vitals.temperature,
                    "respiratory": patient.vitals.respiratory_rate,
                    "alertSeverity": patient.alert_severity,
                    "timestamp": patient.vitals.timestamp
                }
                await websocket.send_json(vitals_data)
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for patient {patient_id}")
    except Exception as e:
        logger.error(f"WebSocket error for patient {patient_id}: {e}")
    finally:
        # Remove from active connections
        if patient_id in active_connections:
            active_connections[patient_id].remove(websocket)
            if not active_connections[patient_id]:
                del active_connections[patient_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
