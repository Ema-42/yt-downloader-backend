# CLAUDE.md — Backend (FastAPI)

## Propósito
API REST para descargar videos/audio de YouTube. Uso personal, sin base de datos, sin autenticación.

## Stack
- Python 3.11+, FastAPI 0.146, uvicorn
- `yt-dlp==2026.8.19` como librería Python (nunca subprocess/binario externo)
- `imageio-ffmpeg>=0.5.1` — ffmpeg bundleado, sin instalación del sistema
- `APScheduler==3.11.3` — limpieza automática de archivos viejos
- `pydantic-settings==2.16` — configuración desde `.env`

## Cómo levantar
```bash
cd backend
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Variables de entorno (.env)
```
DOWNLOADS_DIR=downloads
MAX_FILE_AGE_HOURS=2
MAX_FILESIZE_MB=500
COOKIES_FROM_BROWSER=chrome
```

## Estructura de carpetas
```
backend/
├── app/
│   ├── main.py                  # FastAPI app, CORS, lifespan, APScheduler
│   ├── api/routes/
│   │   ├── info.py              # POST /api/info
│   │   └── download.py          # Sistema de jobs + SSE + cancel
│   ├── services/
│   │   ├── ytdlp_service.py     # lógica yt-dlp con progress_hook
│   │   └── cleanup_service.py   # limpieza de archivos viejos
│   ├── schemas/video.py         # Pydantic models (InfoRequest, VideoInfo, DownloadRequest…)
│   └── core/config.py           # Settings desde .env
├── downloads/                   # archivos temporales (ignorados en git)
├── requirements.txt
└── .env
```

## Endpoints implementados

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/info` | Metadata del video (título, thumbnail, formatos, duración, autor) |
| POST | `/api/download` | Inicia descarga async → `{ job_id }` |
| GET | `/api/download/progress/{job_id}` | SSE: progreso en tiempo real (`status`, `progress`, `speed`, `eta`) |
| GET | `/api/download/file/{job_id}` | Sirve el archivo descargado (FileResponse) |
| DELETE | `/api/download/{job_id}` | Cancela una descarga en curso |

## Sistema de jobs (download.py)
- `_jobs: dict[str, dict]` en memoria — no persiste entre reinicios
- El download corre en `threading.Thread` (daemon=True)
- `progress_hook` de yt-dlp actualiza el dict; si `job["cancelled"] == True` lanza excepción para abortar
- SSE endpoint hace polling del dict cada 500ms con `asyncio.sleep`
- Status flow: `starting → downloading → processing → done | error | cancelled`

## Bot-detection de YouTube
- Estrategia principal: `extractor_args: {youtube: {player_client: ['android', 'web']}}`
  - Simula el cliente Android de YouTube, evita el anti-bot sin cookies
  - No requiere mantenimiento en condiciones normales
- Fallback: si el video requiere auth (edad/región/privado), reintenta con `cookiesfrombrowser: (chrome,)`
  - Requiere que Chrome esté cerrado para acceder a su BD de cookies
- Opcional: colocar `cookies.txt` exportado desde el browser en la raíz del backend

## Reglas importantes
- **Nunca** usar `subprocess` o `shell=True` con la URL del usuario
- Validar URL con regex antes de pasarla a yt-dlp (`validate_youtube_url`)
- Errores de yt-dlp → respuestas HTTP claras (400/422), nunca stack traces al cliente
- CORS abierto a `*` (uso local personal)
- ffmpeg: siempre usar `imageio_ffmpeg.get_ffmpeg_exe()` como `ffmpeg_location`

## Actualizar yt-dlp (YouTube cambia seguido)
```bash
pip install -U yt-dlp
```
