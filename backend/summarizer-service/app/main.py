import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import get_settings
from app.elasticsearch_client import es_client
from app.summarizer import summarizer

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Mock patient data for fallback
MOCK_PATIENTS = {
    "P001": "John Smith",
    "P002": "Sarah Johnson", 
    "P003": "Michael Brown",
    "P004": "Emily Davis",
    "P005": "Robert Wilson",
    "P006": "Jennifer Martinez",
    "P007": "David Lee",
    "P008": "Lisa Anderson",
    "P009": "James Taylor",
    "P010": "Maria Garcia"
}


async def generate_summaries_task():
    """Background task to periodically generate summaries."""
    while True:
        try:
            logger.info("Starting summary generation cycle")
            
            # Get all patients
            patients = es_client.get_all_patients()
            
            if not patients:
                # Use mock patients if Elasticsearch is not available
                patients = list(MOCK_PATIENTS.keys())
            
            for patient_id in patients:
                try:
                    # Get patient data from Elasticsearch
                    vitals = es_client.get_patient_vitals(patient_id, settings.vitals_lookback_minutes)
                    alerts = es_client.get_patient_alerts(patient_id, settings.vitals_lookback_minutes)
                    
                    # Get patient name
                    patient_name = MOCK_PATIENTS.get(patient_id, f"Patient {patient_id}")
                    if vitals and vitals[0].get("patient_name"):
                        patient_name = vitals[0].get("patient_name")
                    
                    # Generate summary
                    summary = summarizer.generate_summary(patient_id, patient_name, vitals, alerts)
                    
                    # Save to Elasticsearch
                    es_client.save_summary(
                        patient_id=patient_id,
                        patient_name=patient_name,
                        summary=summary["text"],
                        vitals_count=summary["vitals_count"],
                        alerts_count=summary["alerts_count"],
                        processing_time_ms=summary["processing_time_ms"]
                    )
                    
                except Exception as e:
                    logger.error(f"Error generating summary for patient {patient_id}: {e}")
            
            logger.info(f"Completed summary generation for {len(patients)} patients")
            
        except Exception as e:
            logger.error(f"Error in summary generation task: {e}")
        
        await asyncio.sleep(settings.summary_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    # Start background summary generation task
    task = asyncio.create_task(generate_summaries_task())
    
    yield
    
    # Cleanup
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    logger.info("Shutting down summarizer service")


# Create FastAPI app
app = FastAPI(
    title="Medical Summarizer Service",
    description="AI-powered clinical summary generation using DistilBART",
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


class SummaryRequest(BaseModel):
    patientId: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    model_info = summarizer.get_model_info()
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version,
        "elasticsearch": es_client.health_check(),
        "model_loaded": model_info["loaded"],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/summaries")
async def get_all_summaries():
    """Get all generated summaries."""
    summaries = summarizer.get_all_summaries()
    
    # Also try to get from Elasticsearch
    if not summaries:
        for patient_id, patient_name in MOCK_PATIENTS.items():
            cached = es_client.get_latest_summary(patient_id)
            if cached:
                summaries.append({
                    "patient_id": cached.get("patient_id"),
                    "text": cached.get("summary_text"),
                    "timestamp": cached.get("@timestamp"),
                    "model_name": cached.get("model_name"),
                    "model_version": cached.get("model_version")
                })
    
    return summaries


@app.get("/api/summaries/{patient_id}")
async def get_patient_summary(patient_id: str):
    """Get summary for a specific patient."""
    # Check cache first
    summary = summarizer.get_summary(patient_id)
    
    if summary:
        return summary
    
    # Check Elasticsearch
    cached = es_client.get_latest_summary(patient_id)
    if cached:
        return {
            "patient_id": cached.get("patient_id"),
            "text": cached.get("summary_text"),
            "timestamp": cached.get("@timestamp"),
            "model_name": cached.get("model_name"),
            "model_version": cached.get("model_version")
        }
    
    # Generate new summary
    vitals = es_client.get_patient_vitals(patient_id, settings.vitals_lookback_minutes)
    alerts = es_client.get_patient_alerts(patient_id, settings.vitals_lookback_minutes)
    patient_name = MOCK_PATIENTS.get(patient_id, f"Patient {patient_id}")
    
    summary = summarizer.generate_summary(patient_id, patient_name, vitals, alerts)
    return summary


@app.get("/api/model/info")
async def get_model_info():
    """Get model information."""
    return summarizer.get_model_info()


@app.post("/api/model/trigger-summary")
async def trigger_summary(request: SummaryRequest, background_tasks: BackgroundTasks):
    """Trigger manual summary generation for a patient."""
    patient_id = request.patientId
    
    vitals = es_client.get_patient_vitals(patient_id, settings.vitals_lookback_minutes)
    alerts = es_client.get_patient_alerts(patient_id, settings.vitals_lookback_minutes)
    patient_name = MOCK_PATIENTS.get(patient_id, f"Patient {patient_id}")
    
    summary = summarizer.generate_summary(patient_id, patient_name, vitals, alerts)
    
    # Save to Elasticsearch in background
    background_tasks.add_task(
        es_client.save_summary,
        patient_id=patient_id,
        patient_name=patient_name,
        summary=summary["text"],
        vitals_count=summary["vitals_count"],
        alerts_count=summary["alerts_count"],
        processing_time_ms=summary["processing_time_ms"]
    )
    
    return {"status": "generated", "summary": summary}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
