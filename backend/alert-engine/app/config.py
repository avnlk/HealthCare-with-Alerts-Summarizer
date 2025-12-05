from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service info
    service_name: str = "alert-engine"
    service_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8002
    
    # Elasticsearch settings
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_user: str = "elastic"
    elasticsearch_password: str = ""
    elasticsearch_alert_index: str = "medical-alerts"
    elasticsearch_vitals_index: str = "medical-vitals"
    
    # Vitals service
    vitals_service_url: str = "http://localhost:8001"
    
    # Alert thresholds
    hr_low_critical: int = 40
    hr_low_warning: int = 50
    hr_high_warning: int = 100
    hr_high_critical: int = 130
    
    spo2_critical: int = 88
    spo2_warning: int = 92
    
    bp_systolic_warning: int = 140
    bp_systolic_critical: int = 180
    bp_systolic_low_warning: int = 90
    bp_systolic_low_critical: int = 80
    
    temp_warning: float = 38.0
    temp_critical: float = 39.0
    temp_low_warning: float = 35.5
    temp_low_critical: float = 35.0
    
    resp_high_warning: int = 24
    resp_high_critical: int = 30
    resp_low_warning: int = 10
    resp_low_critical: int = 8
    
    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
