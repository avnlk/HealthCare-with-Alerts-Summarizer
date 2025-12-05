import logging
from datetime import datetime
from typing import Optional
from elasticsearch import Elasticsearch
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Elasticsearch client for logging medical alerts."""
    
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
        """Create index template for medical alerts."""
        template_name = "medical-alerts-template"
        template_body = {
            "index_patterns": ["medical-alerts-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "alert_id": {"type": "keyword"},
                        "patient_id": {"type": "keyword"},
                        "alert_type": {"type": "keyword"},
                        "message": {"type": "text"},
                        "severity": {"type": "keyword"},
                        "vital_type": {"type": "keyword"},
                        "vital_value": {"type": "float"},
                        "threshold": {"type": "float"},
                        "acknowledged": {"type": "boolean"},
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
    
    def log_alert(self, alert: dict):
        """Log alert to Elasticsearch."""
        if not self.connected or not self.client:
            return
        
        try:
            index_name = f"{settings.elasticsearch_alert_index}-{datetime.now().strftime('%Y.%m.%d')}"
            
            doc = {
                "@timestamp": datetime.now().isoformat(),
                "alert_id": alert.get("id"),
                "patient_id": alert.get("patient_id"),
                "alert_type": alert.get("type"),
                "message": alert.get("message"),
                "severity": alert.get("severity"),
                "vital_type": alert.get("vital_type"),
                "vital_value": alert.get("vital_value"),
                "threshold": alert.get("threshold"),
                "acknowledged": alert.get("acknowledged", False),
                "service": settings.service_name
            }
            
            self.client.index(index=index_name, document=doc)
            
        except Exception as e:
            logger.error(f"Failed to log alert to Elasticsearch: {e}")
    
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
