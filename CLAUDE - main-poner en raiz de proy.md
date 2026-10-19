# CLAUDE.md — YT Downloader (Monorepo)

## Qué es esto
App personal para descargar videos y audio de YouTube. Dos proyectos en esta carpeta:

| Carpeta | Stack | Puerto |
|---------|-------|--------|
| `backend/` | FastAPI + yt-dlp | 8000 |
| `frontend/` | Next.js + Tailwind | 3005 |

## Cómo levantar (dos terminales)

**Terminal 1 — Backend:**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev   # puerto 3005 (definido en package.json y .env.local)
```

## Estado del proyecto (Oct 2026) — TODO IMPLEMENTADO

### Backend ✅
- `POST /api/info` — metadata del video (título, thumbnail, formatos, duración, autor)
- `POST /api/download` — inicia descarga async, devuelve `{ job_id }`
- `GET /api/download/progress/{job_id}` — SSE con progreso en tiempo real (%, velocidad, ETA)
- `GET /api/download/file/{job_id}` — sirve el archivo terminado
- `DELETE /api/download/{job_id}` — cancela la descarga
- `GET /health` — health check
- Bot-detection de YouTube resuelto con `player_client: ['android', 'web']`
- ffmpeg bundleado vía `imageio-ffmpeg` (sin instalación del sistema)
- Limpieza automática de `downloads/` cada hora (APScheduler)

### Frontend ✅
- Cola de descargas: múltiples URLs en fila, se ejecutan una tras otra
- Drag-and-drop para reordenar ítems pendientes en la cola
- Barra de progreso real (%, velocidad MB/s, ETA) vía EventSource/SSE
- Botón Cancelar descarga activa
- Nombre de archivo editable antes de descargar (precargado con título del video)
- Historial en localStorage: re-descargar, eliminar, copiar link del video
- Botón "Pegar Link" en la misma fila que Buscar; auto-búsqueda al pegar URL de YouTube
- Iconos con `lucide-react` (sin emojis)
- Dark mode con Tailwind

## Decisiones de diseño
- **Sin base de datos** — historial vive en localStorage del navegador
- **Sin Docker** — dos terminales, ejecución directa
- **Sin autenticación** — uso personal, 100% anónimo
- **yt-dlp como librería** — nunca subprocess ni shell=True con URLs del usuario
- **Jobs en memoria** — dict en-proceso, se pierde al reiniciar el backend (aceptable para uso personal)
- Compartir: `navigator.share()` con fallback a portapapeles; URL = `localhost:3005/?v=<yt_url>`

## Notas de mantenimiento
- Actualizar yt-dlp cuando YouTube rompa la extracción: `pip install -U yt-dlp`
- Documentación detallada de cada proyecto en `backend/CLAUDE.md` y `frontend/CLAUDE.md`
