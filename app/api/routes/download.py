import asyncio
import json
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse

from app.schemas.video import DownloadRequest
from app.services.ytdlp_service import download_audio, download_video, validate_youtube_url

router = APIRouter()

_jobs: dict[str, dict] = {}
_lock = threading.Lock()


def _new_job() -> dict:
    return {
        "status": "starting",
        "progress": 0.0,
        "speed": None,
        "eta": None,
        "file": None,
        "error": None,
        "cancelled": False,
    }


def _make_progress_hook(job_id: str):
    def hook(d: dict) -> None:
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return
            if job["cancelled"]:
                raise Exception("Descarga cancelada por el usuario.")
            s = d.get("status")
            if s == "downloading":
                downloaded = d.get("downloaded_bytes") or 0
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                job["status"] = "downloading"
                job["progress"] = round(downloaded / total * 100, 1) if total else 0.0
                job["speed"] = d.get("speed")
                job["eta"] = d.get("eta")
            elif s == "finished":
                job["status"] = "processing"
                job["progress"] = 100.0
    return hook


@router.post("/download")
def start_download(body: DownloadRequest):
    if not validate_youtube_url(body.url):
        raise HTTPException(status_code=400, detail="URL de YouTube inválida.")

    job_id = uuid.uuid4().hex
    with _lock:
        _jobs[job_id] = _new_job()

    def run() -> None:
        hook = _make_progress_hook(job_id)
        try:
            if body.type == "audio":
                path = download_audio(body.url, hook)
            else:
                path = download_video(body.url, body.format_id, hook)
            with _lock:
                job = _jobs.get(job_id)
                if job and not job["cancelled"]:
                    job["status"] = "done"
                    job["file"] = path
                    job["progress"] = 100.0
        except Exception as exc:
            with _lock:
                job = _jobs.get(job_id)
                if job:
                    if job["cancelled"]:
                        job["status"] = "cancelled"
                    else:
                        job["status"] = "error"
                        job["error"] = _clean(str(exc))

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@router.get("/download/progress/{job_id}")
async def stream_progress(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado.")

    async def gen():
        while True:
            with _lock:
                job = _jobs.get(job_id)
            if not job:
                yield f"data: {json.dumps({'status': 'error', 'error': 'Job no encontrado'})}\n\n"
                break
            payload = {
                "status": job["status"],
                "progress": job["progress"],
                "speed": job["speed"],
                "eta": job["eta"],
                "error": job["error"],
            }
            yield f"data: {json.dumps(payload)}\n\n"
            if job["status"] in ("done", "error", "cancelled"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/download/file/{job_id}")
def get_file(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado.")
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail="Descarga aún en progreso.")
    path: Path = job["file"]
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    ext = path.suffix.lower()
    media = "audio/mpeg" if ext == ".mp3" else "video/mp4"
    return FileResponse(
        path=str(path),
        media_type=media,
        filename=path.name,
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )


@router.delete("/download/{job_id}")
def cancel_job(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job no encontrado.")
        job["cancelled"] = True
    return {"ok": True}


def _clean(msg: str) -> str:
    if "ERROR:" in msg:
        return msg.split("ERROR:")[-1].strip()
    return msg
