from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import download, info
from app.core.config import settings
from app.services.cleanup_service import cleanup_old_files

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(cleanup_old_files, "interval", hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="YT Downloader API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(info.router, prefix="/api")
app.include_router(download.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
