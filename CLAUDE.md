# CLAUDE.md — Backend (FastAPI)

## Propósito
API REST para descargar videos/audio de YouTube. Uso personal, sin base de datos, sin autenticación.

## Stack
- Python 3.11+, FastAPI, uvicorn
- `yt-dlp` como librería Python (nunca subprocess/binario externo)
- `ffmpeg` para conversión de audio a mp3
- `python-dotenv` para variables de entorno

## Cómo levantar
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Variables de entorno (.env)
Copiar `.env.example` a `.env`:
```
CORS_ORIGINS=http://localhost:3000
DOWNLOADS_DIR=downloads
MAX_FILE_AGE_HOURS=2
MAX_FILESIZE_MB=500
```

## Estructura de carpetas
```
backend/
├── app/
│   ├── main.py               # FastAPI app, CORS, routers
│   ├── api/routes/
│   │   ├── info.py           # POST /api/info
│   │   └── download.py       # POST /api/download
│   ├── services/
│   │   ├── ytdlp_service.py  # lógica yt-dlp
│   │   └── cleanup_service.py# limpieza de archivos viejos
│   ├── schemas/              # Pydantic models
│   └── core/
│       └── config.py         # Settings desde .env
├── downloads/                # archivos temporales (ignorados en git)
├── requirements.txt
└── .env.example
```

## Endpoints implementados / pendientes

| Estado | Método | Ruta | Descripción |
|--------|--------|------|-------------|
| ✅ | GET | `/health` | Health check |
| ❌ | POST | `/api/info` | Metadata del video (título, thumbnail, formatos) |
| ❌ | POST | `/api/download` | Descarga video o audio como StreamingResponse |

## Reglas importantes
- **Nunca** usar `subprocess` o `shell=True` con la URL del usuario
- Validar que la URL sea de `youtube.com` o `youtu.be` con regex antes de pasarla a yt-dlp
- Errores de yt-dlp → respuestas HTTP claras (400/404/422), nunca stack traces al cliente
- No hay base de datos — `SQLAlchemy`, `alembic`, `asyncpg` en requirements.txt son residuos; no usarlos
- Limpiar archivos en `downloads/` con más de `MAX_FILE_AGE_HOURS` horas

## Actualizar yt-dlp (YouTube cambia seguido)
```bash
pip install -U yt-dlp
```

## Estado actual (Oct 2026)
- `main.py` básico con CORS hacia `localhost:3000` ✅
- `yt-dlp==2026.8.19` instalado ✅
- Rutas `/api/info` y `/api/download` → **pendientes**
- `ytdlp_service.py`, `cleanup_service.py`, schemas → **pendientes**
