# SmartStore ERP — Configuration
# Ye file saari settings ek jagah rakhti hai (DB path, secret key, app name, etc.)

from pydantic import BaseModel


class Settings(BaseModel):
    # App Info
    APP_NAME: str = "SmartStore ERP"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Native, India-First FMCG ERP for Small Malls & Wholesale"

    # Database — Phase 1 mein SQLite, Phase 15 mein PostgreSQL switch karenge
    DATABASE_URL: str = "sqlite:///./smartstore.db"

    # JWT Auth — Phase 2 mein login ke liye use hoga
    SECRET_KEY: str = "smartstore-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours — full shift ke liye

    # CORS — Frontend (HTML file) ko backend se baat karne dega
    CORS_ORIGINS: list[str] = ["*"]  # Phase 1 mein sab allow, production mein restrict karenge

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000


# Ek hi settings object — poore app mein yahi use hoga
settings = Settings()
