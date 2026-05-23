from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://admin:secret@localhost:5432/assessment_db"
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    ai_service_url: str = "http://localhost:8001"
    ai_timeout: int = 60
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
