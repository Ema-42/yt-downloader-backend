from pydantic import BaseModel, HttpUrl
from typing import Literal


class InfoRequest(BaseModel):
    url: str


class FormatInfo(BaseModel):
    format_id: str
    ext: str
    resolution: str | None = None   # ej. "1920x1080"
    note: str | None = None         # ej. "1080p", "bestaudio"
    filesize: int | None = None     # bytes


class VideoInfo(BaseModel):
    title: str
    thumbnail: str | None
    duration: int | None            # segundos
    author: str | None
    video_formats: list[FormatInfo]
    audio_formats: list[FormatInfo]


class DownloadRequest(BaseModel):
    url: str
    type: Literal["video", "audio"]
    format_id: str | None = None
