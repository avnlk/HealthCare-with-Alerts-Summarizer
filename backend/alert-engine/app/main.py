import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

from app.config import get_settings
from app.alerts import alert_engine, Alert
from app.elasticsearch_client import es_client

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def poll_vitals_and_generate_alerts():
    """Background task to poll vitals and generate alerts."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(f"{settings.vitals_service_url}/api/patients", timeout=10.0)
                if response.status_code == 200:
                    patients = response.json()
                    for patient in patients:
                        alerts = alert_engine.analyze_vitals(patient["id"], patient.get("vitals", {}))
                        # Log alerts to Elasticsearch
                        for alert in alerts:
                            es_client.log_alert(alert.model_dump())
            except Exception as e:
                logger.error(f"Error polling vitals: {e}")
            
            await asyncio.sleep(5)  # Poll every 5 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    # Start background polling task
    task = asyncio.create_task(poll_vitals_and_generate_alerts())
    
    yield
    
    # Cleanup
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    logger.info("Shutting down alert engine")


# Create FastAPI app
app = FastAPI(
    title="Alert Engine Service",
    description="Rule-based clinical alert detection service",
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


@app.get("/api/alerts", response_model=None)
async def get_all_alerts() -> List[dict]:
    """Get all active alerts."""
    alerts = alert_engine.get_all_alerts()
    return [alert.model_dump() for alert in alerts]


@app.get("/api/alerts/{patient_id}")
async def get_patient_alerts(patient_id: str) -> List[dict]:
    """Get alerts for a specific patient."""
    alerts = alert_engine.get_patient_alerts(patient_id)
    return [alert.model_dump() for alert in alerts]


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    success = alert_engine.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return {"status": "acknowledged", "alert_id": alert_id}


@app.delete("/api/alerts/{patient_id}")
async def clear_patient_alerts(patient_id: str):
    """Clear all alerts for a patient."""
    alert_engine.clear_patient_alerts(patient_id)
    return {"status": "cleared", "patient_id": patient_id}


@app.post("/api/analyze")
async def analyze_vitals(patient_id: str, vitals: dict):
    """Manually analyze vitals and generate alerts."""
    alerts = alert_engine.analyze_vitals(patient_id, vitals)
    for alert in alerts:
        es_client.log_alert(alert.model_dump())
    return {"alerts": [alert.model_dump() for alert in alerts]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
