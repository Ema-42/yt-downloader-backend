# Backend — YT Downloader

API REST con FastAPI + yt-dlp para descargar videos y audio de YouTube.

## Requisitos

- Python 3.11+
- ffmpeg **no** es necesario instalarlo manualmente — se usa `imageio-ffmpeg` (bundled)

## Instalación

```bash
cd backend
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\activate
# Windows (Git Bash)
source venv/Scripts/activate

pip install -r requirements.txt
```

## Variables de entorno

```bash
cp .env.example .env
```

| Variable | Default | Descripción |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:3005,http://127.0.0.1:3005` | Orígenes permitidos, separados por coma |
| `CORS_ORIGIN_REGEX` | _(vacío)_ | Regex opcional (previews de Vercel) |
| `COOKIES_FILE` | `cookies.txt` | cookies.txt exportado del navegador |
| `COOKIES_FROM_BROWSER` | _(vacío)_ | Solo local: `chrome`, `firefox`, `edge`, `brave` |
| `DOWNLOADS_DIR` | `downloads` | Carpeta de archivos temporales |
| `MAX_FILE_AGE_HOURS` | `2` | Horas antes de borrar archivos viejos |
| `MAX_FILESIZE_MB` | `500` | Límite de tamaño de descarga |

## Levantar el servidor

```bash
uvicorn app.main:app --reload --port 8000
```

API disponible en `http://localhost:8000`. Docs en `http://localhost:8000/docs`.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/info` | Metadata del video (título, formatos, etc.) |
| POST | `/api/download` | Descarga video o audio como archivo |

## Mantener actualizado

YouTube cambia su API seguido. Si las descargas dejan de funcionar:

```bash
pip install -U yt-dlp
```
