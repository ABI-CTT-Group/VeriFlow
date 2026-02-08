# VeriFlow

**Autonomous Research Reliability Engineer** - Convert scientific publications into verifiable, executable computational workflows using Gemini 3 AI agents.

Built for the [Gemini 3 Hackathon](https://gemini3.devpost.com/).

## What It Does

VeriFlow reads a scientific paper (PDF), uses three AI agents powered by Gemini 3 to extract the methodology as an ISA hierarchy, generates executable CWL v1.3 workflows with Dockerfiles, validates them, and runs them via Apache Airflow 3 - all from a single upload.

**Pipeline:** Upload PDF -> Scholar Agent extracts ISA -> User selects assay -> Engineer Agent generates CWL workflow -> Reviewer Agent validates -> Airflow executes -> SDS-compliant results

## Gemini 3 Features Used

| Feature | Usage |
|---------|-------|
| Pydantic Structured Output | All 3 agents use Pydantic schemas as `response_schema` for type-safe JSON |
| Thinking Level Control | HIGH (24576 budget) for Scholar/Engineer, MEDIUM (8192) for Reviewer |
| Grounding with Google Search | Scholar verifies tool names and model references |
| Native PDF Upload | Multimodal publication analysis via `client.files.upload()` |
| Thought Signature Preservation | Multi-turn reasoning chains for iterative generation/validation |
| Agentic Vision | Page image extraction for methodology diagram analysis |

## Architecture

```
Vue 3 Frontend  <-->  FastAPI Backend  <-->  Gemini 3 API (3 Agents)
                            |
              +-------------+-------------+
              |             |             |
          PostgreSQL     MinIO      Airflow 3.0.6
                        (4 buckets)   + Docker-in-Docker
                                      + CWL Runner
```

**10 Docker services**: backend, frontend, postgres, minio, minio-init, airflow-apiserver, airflow-scheduler, dind, cwl

## Quick Start

### Prerequisites

- Docker & Docker Compose
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/ABI-CTT-Group/VeriFlow.git
cd VeriFlow

# 2. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Start all services
docker compose up -d

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API docs: http://localhost:8000/docs
# Airflow UI: http://localhost:8080
# MinIO Console: http://localhost:9001
```

### Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
VeriFlow/
+-- backend/                 # Python FastAPI backend
|   +-- app/
|   |   +-- agents/          # Scholar, Engineer, Reviewer agents
|   |   +-- api/             # REST API routers (5 routers)
|   |   +-- models/          # Pydantic schemas for Gemini structured output
|   |   +-- services/        # GeminiClient, CWLParser, DAGGenerator, etc.
|   |   +-- main.py          # FastAPI entry point
|   +-- config.yaml          # Agent model & thinking level config
|   +-- prompts.yaml         # Versioned prompt templates
|   +-- tests/               # 163 pytest tests
+-- frontend/                # Vue 3 + TypeScript + Tailwind CSS 4
|   +-- src/
|   |   +-- components/      # 16 Vue components
|   |   +-- stores/          # Pinia workflow store
|   |   +-- services/        # API client (axios)
|   |   +-- utils/           # dagre layout
+-- airflow/                 # Custom Airflow 3.0.6 image + DAGs
+-- cwl/                     # CWL runner service (cwltool)
+-- examples/                # Pre-loaded examples (MAMA-MIA)
+-- docker-compose.yml       # 10-service orchestration
+-- .env.example             # Environment variable template
+-- SPEC.md                  # Technical specification
```

## Testing

```bash
# Backend unit tests (163 tests)
cd backend && python -m pytest tests/ -v

# Backend tests in Docker
docker compose run --rm backend pytest tests/ -v

# Frontend tests (6 tests)
cd frontend && npx vitest run
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| AI | Gemini 3 (`google-genai` SDK) - gemini-3-pro-preview, gemini-3-flash-preview |
| Backend | Python 3.11, FastAPI, Pydantic |
| Frontend | Vue 3.5, Vue Flow, Pinia, Tailwind CSS 4, TypeScript, Vite 6 |
| Execution | Apache Airflow 3.0.6, CWL v1.3, Docker-in-Docker |
| Storage | PostgreSQL 15, MinIO (S3-compatible) |
| Standards | ISA-JSON, SPARC SDS, CWL v1.3 |

## Documentation

- [Technical Specification](SPEC.md)
