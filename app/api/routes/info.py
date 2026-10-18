from fastapi import APIRouter, HTTPException
import yt_dlp

from app.schemas.video import InfoRequest, VideoInfo
from app.services.ytdlp_service import get_video_info, validate_youtube_url

router = APIRouter()


@router.post("/info", response_model=VideoInfo)
def get_info(body: InfoRequest):
    if not validate_youtube_url(body.url):
        raise HTTPException(status_code=400, detail="URL de YouTube inválida. Solo se aceptan youtube.com y youtu.be.")

    try:
        return get_video_info(body.url)
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "Private video" in msg:
            raise HTTPException(status_code=404, detail="El video es privado.")
        if "not available" in msg.lower():
            raise HTTPException(status_code=404, detail="El video no está disponible.")
        raise HTTPException(status_code=422, detail=f"No se pudo obtener información del video: {_clean_ydl_error(msg)}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al procesar la URL.")


def _clean_ydl_error(msg: str) -> str:
    # yt-dlp incluye prefijos como "ERROR: [youtube]" — los quitamos
    if "ERROR:" in msg:
        return msg.split("ERROR:")[-1].strip()
    return msg
