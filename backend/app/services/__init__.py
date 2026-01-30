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

# Stage 5: Execution engine services
try:
    from app.services.cwl_parser import cwl_parser, CWLParser
    from app.services.dag_generator import dag_generator, DAGGenerator
    from app.services.airflow_client import airflow_client, AirflowClient
    from app.services.docker_builder import docker_builder, DockerBuilder
    from app.services.execution_engine import execution_engine, ExecutionEngine
    EXECUTION_ENGINE_AVAILABLE = True
except ImportError as e:
    EXECUTION_ENGINE_AVAILABLE = False
    cwl_parser = None
    CWLParser = None
    dag_generator = None
    DAGGenerator = None
    airflow_client = None
    AirflowClient = None
    docker_builder = None
    DockerBuilder = None
    execution_engine = None
    ExecutionEngine = None

__all__ = [
    # Stage 1-2: Core services
    "minio_service",
    "MinIOService",
    "db_service",
    "DatabaseService",
    # Stage 4: Gemini
    "get_gemini_client",
    "GeminiClient",
    "GEMINI_AVAILABLE",
    # Stage 5: Execution engine
    "cwl_parser",
    "CWLParser",
    "dag_generator",
    "DAGGenerator",
    "airflow_client",
    "AirflowClient",
    "docker_builder",
    "DockerBuilder",
    "execution_engine",
    "ExecutionEngine",
    "EXECUTION_ENGINE_AVAILABLE",
]
