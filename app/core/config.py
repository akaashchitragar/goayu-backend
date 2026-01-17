from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # MongoDB Configuration
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "ayushya"
    
    # Google Gemini AI
    GEMINI_API_KEY: str
    
    # Resend Email Service
    RESEND_API_KEY: str = ""
    
    # App Configuration
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    # CORS Origins
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001,https://goayu.life"
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
