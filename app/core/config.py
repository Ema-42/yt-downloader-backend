from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Orígenes permitidos separados por coma (ej: "https://mi-app.vercel.app,http://localhost:3005")
    cors_origins: str = "http://localhost:3005,http://127.0.0.1:3005"
    # Regex opcional para permitir previews de Vercel (ej: "https://.*\.vercel\.app")
    cors_origin_regex: str | None = None
    downloads_dir: Path = Path("downloads")
    max_file_age_hours: int = 2
    max_filesize_mb: int = 500
    # Archivo cookies.txt exportado desde el browser (tiene prioridad)
    cookies_file: str = "cookies.txt"
    # Navegador de fallback si no hay cookies.txt: chrome, firefox, edge, brave.
    # Vacío = desactivado (en servidores no hay navegador instalado).
    cookies_from_browser: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
settings.downloads_dir.mkdir(parents=True, exist_ok=True)
