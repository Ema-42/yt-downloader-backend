import time
from pathlib import Path

from app.core.config import settings


def cleanup_old_files() -> int:
    """Borra archivos en downloads/ más viejos que MAX_FILE_AGE_HOURS. Devuelve cantidad eliminada."""
    max_age_secs = settings.max_file_age_hours * 3600
    now = time.time()
    removed = 0

    for f in settings.downloads_dir.iterdir():
        if f.is_file() and (now - f.stat().st_mtime) > max_age_secs:
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass

    return removed
