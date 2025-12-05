import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from elasticsearch import Elasticsearch
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Elasticsearch client for reading medical data and writing summaries."""
    
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
                self.connected = False
        except Exception as e:
            logger.warning(f"Failed to connect to Elasticsearch: {e}")
            self.connected = False
    
    def _setup_index_template(self):
        """Create index template for medical summaries."""
        template_name = "medical-summaries-template"
        template_body = {
            "index_patterns": ["medical-summaries-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "patient_id": {"type": "keyword"},
                        "patient_name": {"type": "text"},
                        "summary_text": {"type": "text"},
                        "vitals_count": {"type": "integer"},
                        "alerts_count": {"type": "integer"},
                        "model_name": {"type": "keyword"},
                        "model_version": {"type": "keyword"},
                        "processing_time_ms": {"type": "integer"},
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
    
    def get_patient_vitals(self, patient_id: str, minutes: int = 30) -> List[Dict]:
        """Get vitals from medical-vitals-* indices for a patient."""
        if not self.connected or not self.client:
            return []
        
        try:
            now = datetime.now()
            start_time = now - timedelta(minutes=minutes)
            
            query = {
                "bool": {
                    "must": [
                        {"term": {"patient_id": patient_id}},
                        {"range": {"@timestamp": {"gte": start_time.isoformat()}}}
                    ]
                }
            }
            
            response = self.client.search(
                index=settings.elasticsearch_vitals_index,
                query=query,
                size=1000,
                sort=[{"@timestamp": "desc"}]
            )
            
            return [hit["_source"] for hit in response["hits"]["hits"]]
            
        except Exception as e:
            logger.error(f"Failed to get patient vitals: {e}")
            return []
    
    def get_patient_alerts(self, patient_id: str, minutes: int = 30) -> List[Dict]:
        """Get alerts from medical-alerts-* indices for a patient."""
        if not self.connected or not self.client:
            return []
        
        try:
            now = datetime.now()
            start_time = now - timedelta(minutes=minutes)
            
            query = {
                "bool": {
                    "must": [
                        {"term": {"patient_id": patient_id}},
                        {"range": {"@timestamp": {"gte": start_time.isoformat()}}}
                    ]
                }
            }
            
            response = self.client.search(
                index=settings.elasticsearch_alerts_index,
                query=query,
                size=100,
                sort=[{"@timestamp": "desc"}]
            )
            
            return [hit["_source"] for hit in response["hits"]["hits"]]
            
        except Exception as e:
            logger.error(f"Failed to get patient alerts: {e}")
            return []
    
    def get_all_patients(self) -> List[str]:
        """Get unique patient IDs from medical indices."""
        if not self.connected or not self.client:
            return []
        
        try:
            now = datetime.now()
            start_time = now - timedelta(hours=24)
            
            query = {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": start_time.isoformat()}}}
                    ]
                }
            }
            
            aggs = {
                "unique_patients": {
                    "terms": {
                        "field": "patient_id",
                        "size": 1000
                    }
                }
            }
            
            response = self.client.search(
                index=settings.elasticsearch_vitals_index,
                query=query,
                aggs=aggs,
                size=0
            )
            
            buckets = response.get("aggregations", {}).get("unique_patients", {}).get("buckets", [])
            return [bucket["key"] for bucket in buckets]
            
        except Exception as e:
            logger.error(f"Failed to get patient list: {e}")
            return []
    
    def save_summary(self, patient_id: str, patient_name: str, summary: str, 
                     vitals_count: int, alerts_count: int, processing_time_ms: int):
        """Save generated summary to medical-summaries-* index."""
        if not self.connected or not self.client:
            return
        
        try:
            index_name = f"{settings.elasticsearch_summary_index}-{datetime.now().strftime('%Y.%m.%d')}"
            
            doc = {
                "@timestamp": datetime.now().isoformat(),
                "patient_id": patient_id,
                "patient_name": patient_name,
                "summary_text": summary,
                "vitals_count": vitals_count,
                "alerts_count": alerts_count,
                "model_name": settings.model_name,
                "model_version": settings.model_version,
                "processing_time_ms": processing_time_ms,
                "service": settings.service_name
            }
            
            self.client.index(index=index_name, document=doc)
            logger.info(f"Saved summary for patient {patient_id}")
            
        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
    
    def get_latest_summary(self, patient_id: str) -> Optional[Dict]:
        """Get the latest summary for a patient."""
        if not self.connected or not self.client:
            return None
        
        try:
            query = {
                "bool": {
                    "must": [{"term": {"patient_id": patient_id}}]
                }
            }
            
            response = self.client.search(
                index=f"{settings.elasticsearch_summary_index}-*",
                query=query,
                size=1,
                sort=[{"@timestamp": "desc"}]
            )
            
            hits = response["hits"]["hits"]
            if hits:
                return hits[0]["_source"]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest summary: {e}")
            return None
    
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
