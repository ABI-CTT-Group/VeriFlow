"""
VeriFlow Backend - FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import publications, workflows, executions, catalogue
from app.services.database import db_service
from app.services.minio_client import minio_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    try:
        await db_service.connect()
    except Exception as e:
        print(f"Warning: Could not connect to database: {e}")
    
    try:
        minio_service.ensure_buckets_exist()
    except Exception as e:
        print(f"Warning: Could not initialize MinIO buckets: {e}")
    
    yield
    
    # Shutdown
    await db_service.disconnect()


app = FastAPI(
    title="VeriFlow API",
    description="Research Reliability Engineer - API Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(publications.router, prefix="/api/v1", tags=["Publications"])
app.include_router(workflows.router, prefix="/api/v1", tags=["Workflows"])
app.include_router(executions.router, prefix="/api/v1", tags=["Executions"])
app.include_router(catalogue.router, prefix="/api/v1", tags=["Catalogue"])


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "VeriFlow API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "publications": "/api/v1/publications",
            "study_design": "/api/v1/study-design",
            "workflows": "/api/v1/workflows",
            "executions": "/api/v1/executions",
            "catalogue": "/api/v1/catalogue",
            "sources": "/api/v1/sources",
            "websocket": "/api/v1/ws/logs",
        },
    }
