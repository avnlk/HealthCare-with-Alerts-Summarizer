from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service info
    service_name: str = "summarizer-service"
    service_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8003
    
    # Model settings
    model_name: str = "sshleifer/distilbart-cnn-12-6"
    model_version: str = "1.0.0"
    max_input_length: int = 1024
    max_output_length: int = 150
    min_output_length: int = 30
    
    # Elasticsearch settings
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_user: str = "elastic"
    elasticsearch_password: str = ""
    elasticsearch_summary_index: str = "medical-summaries"
    elasticsearch_vitals_index: str = "medical-vitals-*"
    elasticsearch_alerts_index: str = "medical-alerts-*"
    
    # Summarization settings
    summary_interval_seconds: int = 60
    vitals_lookback_minutes: int = 30
    
    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
