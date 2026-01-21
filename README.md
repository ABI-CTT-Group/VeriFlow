# VeriFlow

Autonomous Research Reliability Engineer - Convert scientific papers into verifiable, executable workflows.

## Quick Start

```bash
# Start all services
docker-compose up -d

# Run tests
./scripts/run_all_tests.sh
```

## Project Structure

- `ui/` - Vue 3 + TypeScript frontend
- `backend/` - FastAPI Python backend
- `airflow/` - Airflow DAGs and configuration
- `docker/` - Dockerfiles for services
- `scripts/` - Utility scripts

## Documentation

- [Specification](spec.md)
- [Implementation Plan](PLAN.md)
