"""Application settings and configuration management."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # FCM Configuration
    fcm_project_id: Optional[str] = Field(None, env="FCM_PROJECT_ID")
    fcm_private_key_id: Optional[str] = Field(None, env="FCM_PRIVATE_KEY_ID")
    fcm_private_key: Optional[str] = Field(None, env="FCM_PRIVATE_KEY")
    fcm_client_email: Optional[str] = Field(None, env="FCM_CLIENT_EMAIL")
    
    # Valkey Configuration
    valkey_url: str = Field("redis://localhost:6379", env="VALKEY_URL")
    valkey_db: int = Field(0, env="VALKEY_DB")
    
    # Application Configuration
    app_name: str = Field("notification-service", env="APP_NAME")
    app_version: str = Field("0.1.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # API Configuration
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_prefix: str = Field("/api/v1", env="API_PREFIX")
    
    # Notification Configuration
    max_tokens_per_request: int = Field(500, env="MAX_TOKENS_PER_REQUEST")
    notification_timeout: int = Field(30, env="NOTIFICATION_TIMEOUT")
    
    # Monitoring
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 