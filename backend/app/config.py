from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Encryption
    encryption_key: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 30
    
    # Spotify API
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "moodlens://callback"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # Background Jobs
    ingestion_interval_minutes: int = 15
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
