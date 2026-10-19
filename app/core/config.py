from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:3005"]
    downloads_dir: Path = Path("downloads")
    max_file_age_hours: int = 2
    max_filesize_mb: int = 500
    # Archivo cookies.txt exportado desde el browser (tiene prioridad)
    cookies_file: str = "cookies.txt"
    # Navegador de fallback si no hay cookies.txt: chrome, firefox, edge, brave
    cookies_from_browser: str = "chrome"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
settings.downloads_dir.mkdir(parents=True, exist_ok=True)
