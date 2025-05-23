from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field

class Settings(BaseSettings):
    APP_NAME: str = "FastAPI MongoDB Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # MongoDB settings
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL: int = 3600  # Thời gian cache mặc định (1 giờ)
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }

settings = Settings()