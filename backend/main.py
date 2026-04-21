from contextlib import asynccontextmanager
import mimetypes
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import init_db
from config import settings
from routes import upload, jobs, cleanup
from services.storage import storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if (settings.storage_type or "local").lower() == "local":
        os.makedirs(f"{settings.local_storage_path}/uploads", exist_ok=True)
        os.makedirs(f"{settings.local_storage_path}/shorts", exist_ok=True)
        os.makedirs(f"{settings.local_storage_path}/tmp", exist_ok=True)
    yield


app = FastAPI(title="Video Pipeline API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(cleanup.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"ok": True}


storage_type = (settings.storage_type or "local").lower()

# Serve local shorts/files in dev.
if storage_type == "local":
    app.mount(
        "/storage",
        StaticFiles(directory=settings.local_storage_path),
        name="storage",
    )


if storage_type == "db":
    @app.get("/storage/{key:path}")
    def serve_database_storage(key: str):
        try:
            data = storage.read(key)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")

        media_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        return Response(content=data, media_type=media_type)
