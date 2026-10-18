import re
import uuid
from pathlib import Path

import yt_dlp

from app.core.config import settings
from app.schemas.video import FormatInfo, VideoInfo

_YT_URL_RE = re.compile(
    r"^https?://(www\.)?(youtube\.com/watch\?.*v=[\w-]+|youtu\.be/[\w-]+)"
)


def validate_youtube_url(url: str) -> bool:
    return bool(_YT_URL_RE.match(url.strip()))


def get_video_info(url: str) -> VideoInfo:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    video_formats: list[FormatInfo] = []
    audio_formats: list[FormatInfo] = []

    for f in info.get("formats", []):
        fmt = FormatInfo(
            format_id=f["format_id"],
            ext=f.get("ext", ""),
            resolution=f.get("resolution") or _build_resolution(f),
            note=f.get("format_note"),
            filesize=f.get("filesize") or f.get("filesize_approx"),
        )
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")

        if vcodec != "none" and acodec != "none":
            video_formats.append(fmt)
        elif vcodec != "none":
            video_formats.append(fmt)
        elif acodec != "none":
            audio_formats.append(fmt)

    return VideoInfo(
        title=info.get("title", ""),
        thumbnail=info.get("thumbnail"),
        duration=info.get("duration"),
        author=info.get("uploader"),
        video_formats=video_formats,
        audio_formats=audio_formats,
    )


def download_video(url: str, format_id: str | None) -> Path:
    job_id = uuid.uuid4().hex
    out_tmpl = str(settings.downloads_dir / f"{job_id}.%(ext)s")

    fmt = format_id if format_id else "bestvideo+bestaudio/best"

    ydl_opts = {
        "format": fmt,
        "outtmpl": out_tmpl,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
        "max_filesize": settings.max_filesize_mb * 1024 * 1024,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    matches = list(settings.downloads_dir.glob(f"{job_id}.*"))
    if not matches:
        raise FileNotFoundError("El archivo descargado no se encontró.")
    return matches[0]


def download_audio(url: str) -> Path:
    job_id = uuid.uuid4().hex
    out_tmpl = str(settings.downloads_dir / f"{job_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_tmpl,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    mp3_path = settings.downloads_dir / f"{job_id}.mp3"
    if not mp3_path.exists():
        matches = list(settings.downloads_dir.glob(f"{job_id}.*"))
        if not matches:
            raise FileNotFoundError("El archivo de audio no se encontró.")
        return matches[0]
    return mp3_path


# ── helpers ──────────────────────────────────────────────────────────────────

def _build_resolution(f: dict) -> str | None:
    w, h = f.get("width"), f.get("height")
    if w and h:
        return f"{w}x{h}"
    return None
