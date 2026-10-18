from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import yt_dlp

from app.schemas.video import DownloadRequest
from app.services.ytdlp_service import (
    download_audio,
    download_video,
    validate_youtube_url,
)

router = APIRouter()


@router.post("/download")
def download(body: DownloadRequest):
    if not validate_youtube_url(body.url):
        raise HTTPException(status_code=400, detail="URL de YouTube inválida.")

    try:
        if body.type == "audio":
            file_path = download_audio(body.url)
            media_type = "audio/mpeg"
        else:
            file_path = download_video(body.url, body.format_id)
            media_type = "video/mp4"
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "Private video" in msg:
            raise HTTPException(status_code=404, detail="El video es privado.")
        if "not available" in msg.lower():
            raise HTTPException(status_code=404, detail="El video no está disponible.")
        if "File is larger than max-filesize" in msg:
            raise HTTPException(status_code=422, detail="El archivo supera el tamaño máximo permitido.")
        raise HTTPException(status_code=422, detail=_clean_ydl_error(msg))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado durante la descarga.")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name,
        headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'},
    )


def _clean_ydl_error(msg: str) -> str:
    if "ERROR:" in msg:
        return msg.split("ERROR:")[-1].strip()
    return msg
