"""
VeriFlow - Services Package
"""

from app.services.minio_client import minio_service, MinIOService
from app.services.database import db_service, DatabaseService

# Stage 4: Gemini client
try:
    from app.services.gemini_client import get_gemini_client, GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    get_gemini_client = None
    GeminiClient = None

__all__ = [
    "minio_service",
    "MinIOService",
    "db_service",
    "DatabaseService",
    "get_gemini_client",
    "GeminiClient",
    "GEMINI_AVAILABLE",
]
