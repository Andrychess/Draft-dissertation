from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_path: str = "models/mistral-7b-instruct-v0.1.Q4_K_S.gguf"
    passing_threshold: float = 0.6
    confidence_threshold: float = 0.7
    n_ctx: int = 4096
    n_gpu_layers: int = -1
    host: str = "0.0.0.0"
    port: int = 8001

    class Config:
        env_file = ".env"


settings = Settings()
