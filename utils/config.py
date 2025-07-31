import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    ASSEMBLY_AI_API_KEY: str = "d62ad71a6cf54e02ac000e8c4920819f"
    GEMINI_API_KEY: str = "AIzaSyCQkgYAsflx3ITD4_8XljNOhO2QxxoH52k"
    
    # Application
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001"
    ]
    
    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Supabase Configuration
    SUPABASE_URL: str = "https://vowzqejbmqrpirgfipsps.supabase.co"
    SUPABASE_SERVICE_ROLE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZvd3pxZWpibXFycGlyZ2ZpcHNwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzYwMjczNCwiZXhwIjoyMDY5MTc4NzM0fQ.gjfWOAFIzA1tBudi9wgfP33uYrXf-rw1rqHo8BbOJmc"
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    MAX_CONCURRENT_SESSIONS: int = 10
    
    # AI Configuration
    MAX_CONTEXT_LENGTH: int = 4000
    RESPONSE_TIMEOUT: int = 10
    SUGGESTION_DELAY: int = 2
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            if field_name == 'ALLOWED_ORIGINS':
                return [x.strip() for x in raw_val.split(',')]
            return cls.json_loads(raw_val)


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get settings instance (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 