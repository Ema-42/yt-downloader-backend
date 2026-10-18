from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:3000"]
    downloads_dir: Path = Path("downloads")
    max_file_age_hours: int = 2
    max_filesize_mb: int = 500

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
settings.downloads_dir.mkdir(parents=True, exist_ok=True)
