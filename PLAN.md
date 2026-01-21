# VeriFlow MVP Implementation Plan

> **For AI:** Use `superpowers:executing-plans` skill to implement this plan task-by-task.

**Goal:** Build VeriFlow, an autonomous Research Reliability Engineer that converts scientific papers into verifiable, executable workflows.

**Architecture:** Vue 3 + FastAPI monorepo. PydanticAI agents with Gemini 3 Pro. State in PostgreSQL + MinIO. Execution via Airflow 3 + Docker.

**Tech Stack:** Vue 3, TypeScript, Tailwind, Vue Flow, FastAPI, PydanticAI, Gemini 3 Pro, PostgreSQL, MinIO, Docker, Airflow 3.

---

## 1. Overview

### System Goals
1. **Ingest:** Upload PDF and extract ISA study design (Scholar Agent).
2. **Assemble:** Scholar Agent constructs workflow; user visually verifies.
3. **Build:** Engineer Agent generates CWL + Dockerfiles.
4. **Execute:** Run workflow on Airflow 3 with paper's original data.

### Non-Goals (MVP)
- Multi-user authentication (single user).
- Cloud deployment (local Docker Compose only).
- Workflow engines other than Airflow.

### Key Assumptions
- Docker Daemon accessible via socket or TCP.
- Gemini 3 Pro API key available.
- Reference UI in `planning/UI` used for visual styling only.

### Open Questions / Ambiguities
| Question | Resolution |
|:---|:---|
| What PDF library for text extraction? | **Assumption:** Pass raw PDF bytes to Gemini 3 Pro (native multimodal). |
| How to handle large PDFs? | **Assumption:** Rely on Gemini's 1M+ token context window. |
| Exact CWL schema version? | **Assumption:** CWL v1.2 (latest stable). |

---

## 2. Development Stages

| Stage | Description | Entry Criteria | Exit Criteria |
|:---|:---|:---|:---|
| **1. Foundation** | Project skeleton, Docker infra, DB/storage connections | Plan approved | UI + API running in Docker; health endpoints respond |
| **2. Scholar & ISA** | PDF upload, Gemini extraction, ISA tree visualization | Stage 1 complete | Upload PDF → View extracted ISA in UI |
| **3. Workflow UI** | Vue Flow editor with custom nodes, drag-drop assembly | Stage 2 complete | Construct graph visually; export to JSON |
| **4. Engineer & Execution** | CWL/Dockerfile generation, Docker build, Airflow trigger | Stage 3 complete | Full E2E: Upload → Run → See "Running" status |

---

## 3. Tasks per Stage

### Stage 1: Foundation & Infrastructure

#### AI Tasks
| | ID | Task | Dependencies |
|:---|:---|:---|:---|
| [x] | 1.1 | Create monorepo structure: `/ui`, `/backend`, `/airflow`, `/docker` | None |
| [x] | 1.2 | Write `docker-compose.yml` with Postgres, MinIO, Airflow, API, UI services | 1.1 |
| [x] | 1.3 | Backend: Implement DB connection (async SQLAlchemy) and MinIO client | 1.2 |
| [x] | 1.4 | Backend: Create health endpoint `GET /health` | 1.3 |
| [x] | 1.5 | Frontend: Initialize Vue 3 + Vite + Tailwind project | 1.1 |
| [x] | 1.6 | Frontend: Create base layout (dark theme, sidebar, glassmorphism per UI.png) | 1.5 |
| [x] | 1.7 | Write unit tests for DB connection and MinIO client | 1.3 |
| [x] | 1.8 | Write Playwright E2E test: Load homepage → verify title | 1.6 |

#### Developer Tasks
| | ID | Task |
|:---|:---|:---|
| [ ] | D1.1 | Provide `GEMINI_API_KEY` in `.env` |
| [ ] | D1.2 | Verify Docker Desktop running before tests |

---

### Stage 2: Scholar Agent & Extraction

#### AI Tasks
| | ID | Task | Dependencies |
|:---|:---|:---|:---|
| [ ] | 2.1 | Backend: Implement `POST /projects/upload` (store PDF in MinIO) | Stage 1 |
| [ ] | 2.2 | Backend: Define Pydantic models for ISA (`Investigation`, `Study`, `Assay`, `Tool`, `Model`, `Measurement`) | 2.1 |
| [ ] | 2.3 | Backend: Implement `ScholarAgent` using PydanticAI + Gemini 3 Pro | 2.2 |
| [ ] | 2.4 | Backend: Wire upload → agent → store result in DB | 2.3 |
| [ ] | 2.5 | Frontend: Create Upload component (drag-drop PDF) | Stage 1 |
| [ ] | 2.6 | Frontend: Create Study Design Viewer (tree view of ISA hierarchy) | 2.5 |
| [ ] | 2.7 | Frontend: Wire API call on upload → display ISA tree | 2.4, 2.6 |
| [ ] | 2.8 | Write unit tests for Pydantic ISA models | 2.2 |
| [ ] | 2.9 | Write integration test: Mock Gemini response → verify DB insertion | 2.4 |
| [ ] | 2.10 | Write Playwright E2E: Upload PDF → verify "Extraction Complete" toast → verify tree populated | 2.7 |

#### Developer Tasks
| | ID | Task |
|:---|:---|:---|
| [ ] | D2.1 | Visual verification of ISA tree rendering |

---

### Stage 3: Workflow Assembler UI

#### AI Tasks
| | ID | Task | Dependencies |
|:---|:---|:---|:---|
| [ ] | 3.1 | Frontend: Install `@vue-flow/core`, configure dark theme + custom edge styling | Stage 2 |
| [ ] | 3.2 | Frontend: Implement `ToolNode` component (dynamic input/output handles) | 3.1 |
| [ ] | 3.3 | Frontend: Implement `MeasurementNode` and `ModelNode` components | 3.2 |
| [ ] | 3.4 | Frontend: Implement Catalogue panel (list extracted tools/measurements) | 3.3 |
| [ ] | 3.5 | Frontend: Implement drag-drop from Catalogue to Canvas | 3.4 |
| [ ] | 3.6 | Frontend: Implement Pinia store for graph state → JSON export | 3.5 |
| [ ] | 3.7 | Backend: Implement `GET /projects/{id}/workflow` to retrieve saved graph | 3.6 |
| [ ] | 3.8 | Backend: Implement `POST /projects/{id}/workflow` to save graph JSON | 3.7 |
| [ ] | 3.9 | Write Vitest unit tests for Pinia store actions | 3.6 |
| [ ] | 3.10 | Write Playwright E2E: Open Workflow tab → drag Tool node → drag Input node → connect edge → verify JSON export | 3.8 |

#### Developer Tasks
| | ID | Task |
|:---|:---|:---|
| [ ] | D3.1 | Visual sanity check: Confirm nodes look "ComfyUI-like" (curved wires, dark aesthetic) |

---

### Stage 4: Engineer Agent & Execution

#### AI Tasks
| | ID | Task | Dependencies |
|:---|:---|:---|:---|
| [ ] | 4.1 | Backend: Implement `EngineerAgent` (Input: ToolNode → Output: Dockerfile + CWL) | Stage 3 |
| [ ] | 4.2 | Backend: Implement Docker Build service using Python Docker SDK | 4.1 |
| [ ] | 4.3 | Backend: Implement CWL → Airflow DAG converter | 4.2 |
| [ ] | 4.4 | Backend: Implement `POST /workflow/run` to trigger Airflow DAG | 4.3 |
| [ ] | 4.5 | Backend: Implement `ReviewerAgent` for log analysis and error translation | 4.4 |
| [ ] | 4.6 | Frontend: Add "Run" button to Workflow view | 4.4 |
| [ ] | 4.7 | Frontend: Implement Console component with WebSocket log streaming | 4.6 |
| [ ] | 4.8 | Write unit test for CWL generator (JSON input → expected CWL string) | 4.3 |
| [ ] | 4.9 | Write integration test: Build simple "hello world" Docker image via API | 4.2 |
| [ ] | 4.10 | Write Playwright E2E (Happy Path): Upload PDF → auto-assemble graph → click Run → verify "Running" in Console | 4.7 |

#### Developer Tasks
| | ID | Task |
|:---|:---|:---|
| [ ] | D4.1 | Final E2E verification: Upload real paper → Run → Verify Airflow dashboard shows DAG |

---

## 4. Testing Plan per Stage

### Stage 1: Foundation
| Type | Test | Command |
|:---|:---|:---|
| Unit | DB connection, MinIO client setup | `pytest backend/tests/test_db.py -v` |
| Integration | Docker Compose health | `docker-compose up -d && curl http://localhost:8000/health` |
| E2E | Homepage loads with correct title | `npx playwright test tests/e2e/homepage.spec.ts` |

### Stage 2: Scholar
| Type | Test | Command |
|:---|:---|:---|
| Unit | Pydantic ISA model validation | `pytest backend/tests/test_models.py -v` |
| Integration | Mock Gemini → DB insertion | `pytest backend/tests/test_scholar_integration.py -v` |
| E2E | Upload → Tree populated | `npx playwright test tests/e2e/upload.spec.ts` |

### Stage 3: Workflow UI
| Type | Test | Command |
|:---|:---|:---|
| Unit | Pinia store add/remove node | `npm run test:unit -- stores/workflow.test.ts` |
| E2E | Drag-drop → connect → export JSON | `npx playwright test tests/e2e/workflow.spec.ts` |

### Stage 4: Execution
| Type | Test | Command |
|:---|:---|:---|
| Unit | CWL generator output | `pytest backend/tests/test_cwl_generator.py -v` |
| Integration | Docker build "hello world" | `pytest backend/tests/test_docker_build.py -v` |
| E2E | Full happy path run | `npx playwright test tests/e2e/run.spec.ts` |

---

## 5. Quality Gates

| Stage | "Complete" Definition |
|:---|:---|
| **1** | All containers healthy; `GET /health` returns 200; Homepage loads; All tests pass. |
| **2** | PDF upload stores file in MinIO; ISA tree visible in UI; Mock integration test passes; E2E upload test passes. |
| **3** | Can construct graph with 3+ nodes; Export produces valid JSON; E2E drag-connect test passes. |
| **4** | Run button triggers Airflow DAG; Logs stream to Console; No critical bugs; Full E2E happy path passes. |

---

## 6. Risks and Mitigations

| Risk | Stage | Impact | Mitigation |
|:---|:---|:---|:---|
| Docker-in-Docker fails | 4 | Cannot build images | Mount `/var/run/docker.sock` to backend container; test early |
| Gemini latency >30s | 2 | Poor UX | Implement WebSocket progress streaming from start |
| Airflow DAG generation errors | 4 | Execution fails | Use templated DAG approach first; dynamic generation later |
| Vue Flow styling complexity | 3 | Doesn't match ComfyUI aesthetic | Accept basic dark theme initially; polish CSS in later iteration |
| CWL v1.2 edge cases | 4 | Invalid CWL output | Validate CWL output with `cwltool --validate`; add to integration tests |

---

## 7. Final Review and Handoff

### AI Verification Steps
1. Fresh clone to new directory.
2. Run `docker-compose up -d`.
3. Run full test suite: `./scripts/run_all_tests.sh` (pytest + vitest + playwright).
4. Perform manual walkthrough with sample paper.
5. Verify Airflow dashboard shows triggered DAG.

### Developer Readiness Checklist
- [ ] `PLAN.md` reviewed and approved
- [ ] `.env` file contains `GEMINI_API_KEY`
- [ ] Docker Desktop running
- [ ] All AI tests pass (you can verify with `./scripts/run_all_tests.sh`)
- [ ] Visual inspection of UI matches `planning/UI.png` aesthetic
- [ ] E2E happy path verified manually (optional but recommended)

---

## Appendix: File Structure

```
VeriFlow/
├── ui/                      # Vue 3 frontend
│   ├── src/
│   │   ├── components/      # Vue components
│   │   ├── stores/          # Pinia stores
│   │   └── views/           # Page views
│   └── tests/e2e/           # Playwright tests
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/          # PydanticAI agents
│   │   ├── api/             # Route handlers
│   │   ├── models/          # Pydantic/SQLAlchemy models
│   │   └── services/        # Business logic
│   └── tests/               # pytest tests
├── airflow/                 # Airflow DAGs and config
├── docker/                  # Dockerfiles
├── docker-compose.yml
├── spec.md
├── PLAN.md
└── .env
```
