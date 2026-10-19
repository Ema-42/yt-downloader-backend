import re
import uuid
from pathlib import Path

import imageio_ffmpeg
import yt_dlp

from app.core.config import settings
from app.schemas.video import FormatInfo, VideoInfo

_FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

_YT_URL_RE = re.compile(
    r"^https?://(www\.)?(youtube\.com/watch\?.*v=[\w-]+|youtu\.be/[\w-]+)"
)

# Simula el cliente de la app Android de YouTube — evita el anti-bot sin cookies
_EXTRACTOR_ARGS = {
    "youtube": {
        "player_client": ["android", "web"],
    }
}


def validate_youtube_url(url: str) -> bool:
    return bool(_YT_URL_RE.match(url.strip()))


def _base_opts() -> dict:
    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "extractor_args": _EXTRACTOR_ARGS,
    }
    # Si existe cookies.txt lo usa como refuerzo adicional
    cookies_path = Path(settings.cookies_file)
    if cookies_path.exists():
        opts["cookiefile"] = str(cookies_path)
    return opts


_AUTH_ERRORS = ("Sign in", "age", "region", "not available", "private", "members only")


def _extract_info(url: str) -> dict:
    try:
        with yt_dlp.YoutubeDL({**_base_opts(), "extract_flat": False}) as ydl:
            return ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        # Si falla por restricción de edad/región, reintenta con cookies del browser
        if any(kw.lower() in str(e).lower() for kw in _AUTH_ERRORS):
            fallback = {**_base_opts(), "extract_flat": False,
                        "cookiesfrombrowser": (settings.cookies_from_browser,)}
            with yt_dlp.YoutubeDL(fallback) as ydl:
                return ydl.extract_info(url, download=False)
        raise


def get_video_info(url: str) -> VideoInfo:
    info = _extract_info(url)

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

        if vcodec != "none":
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


def _run_download(ydl_opts: dict, url: str) -> None:
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        if any(kw.lower() in str(e).lower() for kw in _AUTH_ERRORS):
            fallback = {**ydl_opts, "cookiesfrombrowser": (settings.cookies_from_browser,)}
            with yt_dlp.YoutubeDL(fallback) as ydl:
                ydl.download([url])
        else:
            raise


def download_video(url: str, format_id: str | None, progress_hook=None) -> Path:
    job_id = uuid.uuid4().hex
    out_tmpl = str(settings.downloads_dir / f"{job_id}.%(ext)s")
    fmt = format_id if format_id else "bestvideo+bestaudio/best"

    ydl_opts = {
        **_base_opts(),
        "format": fmt,
        "outtmpl": out_tmpl,
        "merge_output_format": "mp4",
        "max_filesize": settings.max_filesize_mb * 1024 * 1024,
        "ffmpeg_location": _FFMPEG_PATH,
        "progress_hooks": [progress_hook] if progress_hook else [],
    }
    _run_download(ydl_opts, url)

    matches = list(settings.downloads_dir.glob(f"{job_id}.*"))
    if not matches:
        raise FileNotFoundError("El archivo descargado no se encontró.")
    return matches[0]


def download_audio(url: str, progress_hook=None) -> Path:
    job_id = uuid.uuid4().hex
    out_tmpl = str(settings.downloads_dir / f"{job_id}.%(ext)s")

    ydl_opts = {
        **_base_opts(),
        "format": "bestaudio/best",
        "outtmpl": out_tmpl,
        "ffmpeg_location": _FFMPEG_PATH,
        "progress_hooks": [progress_hook] if progress_hook else [],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    _run_download(ydl_opts, url)

    mp3_path = settings.downloads_dir / f"{job_id}.mp3"
    if not mp3_path.exists():
        matches = list(settings.downloads_dir.glob(f"{job_id}.*"))
        if not matches:
            raise FileNotFoundError("El archivo de audio no se encontró.")
        return matches[0]
    return mp3_path


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_resolution(f: dict) -> str | None:
    w, h = f.get("width"), f.get("height")
    if w and h:
        return f"{w}x{h}"
    return None
