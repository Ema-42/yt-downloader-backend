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
CORS_ORIGINS=http://localhost:3005          # separados por coma; en prod, la URL de Vercel
CORS_ORIGIN_REGEX=                          # opcional, previews de Vercel
DOWNLOADS_DIR=downloads
MAX_FILE_AGE_HOURS=2
MAX_FILESIZE_MB=500
COOKIES_FILE=cookies.txt                    # en Render: /etc/secrets/cookies.txt
COOKIES_FROM_BROWSER=chrome                 # solo local; vacío en servidores
```

## Deploy en Render
- `render.yaml` incluido (Blueprint). Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Setear `CORS_ORIGINS` con la URL de Vercel en el dashboard
- Las IPs de datacenter suelen recibir "Sign in to confirm you're not a bot": subir un `cookies.txt` como **Secret File** (`/etc/secrets/cookies.txt`), idealmente de una cuenta secundaria
- Plan free: se duerme tras 15 min (primer request tarda ~50 s), disco efímero, jobs en memoria se pierden al reiniciar
- Mantener 1 solo worker (los jobs viven en memoria del proceso)

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
- **No forzar `player_client`**: dejar que yt-dlp elija los clientes. Forzar `android,web` limitaba a 360p sin cookies y fallaba con cookies
- YouTube exige resolver desafíos JS: `yt-dlp-ejs` + runtime JS (`js_runtimes: {deno, node}`; `deno` viene por pip)
- En servidores (Render) la IP está marcada → hace falta `cookies.txt` (Secret File, `COOKIES_FILE=/etc/secrets/cookies.txt`)
  - Exportar desde incógnito tras abrir `youtube.com/robots.txt`, luego cerrar la ventana (evita la rotación de cookies)
- Fallback local opcional: `COOKIES_FROM_BROWSER=chrome` (requiere Chrome cerrado); si falla, se muestra el error original

## Reglas importantes
- **Nunca** usar `subprocess` o `shell=True` con la URL del usuario
- Validar URL con regex antes de pasarla a yt-dlp (`validate_youtube_url`)
- Errores de yt-dlp → respuestas HTTP claras (400/422), nunca stack traces al cliente
- CORS restringido a `CORS_ORIGINS` (+ `CORS_ORIGIN_REGEX` opcional)
- `cookies.txt` nunca se commitea (está en `.gitignore`); se copia a un temp escribible al arrancar
- ffmpeg: siempre usar `imageio_ffmpeg.get_ffmpeg_exe()` como `ffmpeg_location`

## Actualizar yt-dlp (YouTube cambia seguido)
```bash
pip install -U yt-dlp
```
