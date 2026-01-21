from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.storage import get_minio
from app.api import health, projects


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    await init_db()
    minio = get_minio()
    minio.ensure_bucket()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="VeriFlow API",
    description="Autonomous Research Reliability Engineer",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
