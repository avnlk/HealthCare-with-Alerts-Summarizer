import logging
import json
from datetime import datetime
from typing import Optional
from elasticsearch import Elasticsearch, helpers
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Elasticsearch client for logging medical vitals."""
    
    def __init__(self):
        self.client: Optional[Elasticsearch] = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Establish connection to Elasticsearch."""
        try:
            if settings.elasticsearch_password:
                self.client = Elasticsearch(
                    settings.elasticsearch_url,
                    basic_auth=(settings.elasticsearch_user, settings.elasticsearch_password),
                    verify_certs=False,
                    request_timeout=30
                )
            else:
                self.client = Elasticsearch(
                    settings.elasticsearch_url,
                    verify_certs=False,
                    request_timeout=30
                )
            
            if self.client.ping():
                self.connected = True
                logger.info(f"Connected to Elasticsearch at {settings.elasticsearch_url}")
                self._setup_index_template()
            else:
                logger.warning("Elasticsearch ping failed")
                self.connected = False
        except Exception as e:
            logger.warning(f"Failed to connect to Elasticsearch: {e}")
            self.connected = False
    
    def _setup_index_template(self):
        """Create index template for medical vitals."""
        template_name = "medical-vitals-template"
        template_body = {
            "index_patterns": ["medical-vitals-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "index.lifecycle.name": "medical-vitals-policy",
                    "index.lifecycle.rollover_alias": "medical-vitals"
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "patient_id": {"type": "keyword"},
                        "patient_name": {"type": "text"},
                        "bed_number": {"type": "keyword"},
                        "heart_rate": {"type": "integer"},
                        "spo2": {"type": "integer"},
                        "systolic_bp": {"type": "integer"},
                        "diastolic_bp": {"type": "integer"},
                        "temperature": {"type": "float"},
                        "respiratory_rate": {"type": "integer"},
                        "alert_severity": {"type": "keyword"},
                        "service": {"type": "keyword"}
                    }
                }
            }
        }
        
        try:
            self.client.indices.put_index_template(name=template_name, body=template_body)
            logger.info(f"Created index template: {template_name}")
        except Exception as e:
            logger.warning(f"Failed to create index template: {e}")
    
    def log_vitals(self, patient: dict):
        """Log patient vitals to Elasticsearch."""
        if not self.connected or not self.client:
            return
        
        try:
            index_name = f"{settings.elasticsearch_index_prefix}-{datetime.now().strftime('%Y.%m.%d')}"
            
            doc = {
                "@timestamp": datetime.now().isoformat(),
                "patient_id": patient.get("id"),
                "patient_name": patient.get("name"),
                "bed_number": patient.get("bed_number") or patient.get("bedNumber"),
                "heart_rate": patient.get("vitals", {}).get("heart_rate") or patient.get("vitals", {}).get("heartRate"),
                "spo2": patient.get("vitals", {}).get("spo2") or patient.get("vitals", {}).get("spO2"),
                "systolic_bp": patient.get("vitals", {}).get("blood_pressure", {}).get("systolic") or 
                               patient.get("vitals", {}).get("bloodPressure", {}).get("systolic"),
                "diastolic_bp": patient.get("vitals", {}).get("blood_pressure", {}).get("diastolic") or
                                patient.get("vitals", {}).get("bloodPressure", {}).get("diastolic"),
                "temperature": patient.get("vitals", {}).get("temperature"),
                "respiratory_rate": patient.get("vitals", {}).get("respiratory_rate") or 
                                    patient.get("vitals", {}).get("respiratory"),
                "alert_severity": patient.get("alert_severity") or patient.get("alertSeverity"),
                "service": settings.service_name
            }
            
            self.client.index(index=index_name, document=doc)
            
        except Exception as e:
            logger.error(f"Failed to log vitals to Elasticsearch: {e}")
    
    def bulk_log_vitals(self, patients: list):
        """Bulk log multiple patient vitals."""
        if not self.connected or not self.client:
            return
        
        try:
            index_name = f"{settings.elasticsearch_index_prefix}-{datetime.now().strftime('%Y.%m.%d')}"
            
            actions = []
            for patient in patients:
                vitals = patient.get("vitals", {})
                bp = vitals.get("blood_pressure", {}) or vitals.get("bloodPressure", {})
                
                doc = {
                    "_index": index_name,
                    "_source": {
                        "@timestamp": datetime.now().isoformat(),
                        "patient_id": patient.get("id"),
                        "patient_name": patient.get("name"),
                        "bed_number": patient.get("bed_number") or patient.get("bedNumber"),
                        "heart_rate": vitals.get("heart_rate") or vitals.get("heartRate"),
                        "spo2": vitals.get("spo2") or vitals.get("spO2"),
                        "systolic_bp": bp.get("systolic"),
                        "diastolic_bp": bp.get("diastolic"),
                        "temperature": vitals.get("temperature"),
                        "respiratory_rate": vitals.get("respiratory_rate") or vitals.get("respiratory"),
                        "alert_severity": patient.get("alert_severity") or patient.get("alertSeverity"),
                        "service": settings.service_name
                    }
                }
                actions.append(doc)
            
            if actions:
                helpers.bulk(self.client, actions)
                
        except Exception as e:
            logger.error(f"Failed to bulk log vitals: {e}")
    
    def health_check(self) -> bool:
        """Check Elasticsearch connection health."""
        if not self.client:
            return False
        try:
            return self.client.ping()
        except:
            return False


# Singleton instance
es_client = ElasticsearchClient()
