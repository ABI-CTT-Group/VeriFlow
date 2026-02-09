# VeriFlow Technical Specification

**Version**: 2.0.0
**Status**: Implementation Specification
**Last Updated**: 2026-02-09
**Target**: Engineers and AI Agents
**Hackathon**: [Gemini 3 Hackathon](https://gemini3.devpost.com/)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Data Structures](#3-data-structures)
4. [Agent System](#4-agent-system)
5. [Gemini 3 Integration](#5-gemini-3-integration)
6. [API Specification](#6-api-specification)
7. [Frontend Specification](#7-frontend-specification)
8. [Execution Engine](#8-execution-engine)
9. [Storage System](#9-storage-system)
10. [Testing](#10-testing)
11. [Error Handling](#11-error-handling)

---

## 1. System Overview

### 1.1 Purpose

VeriFlow is an autonomous Research Reliability Engineer that:
1. Ingests scientific publications (PDF)
2. Extracts methodological logic using AI agents powered by Gemini 3
3. Creates verifiable, executable research workflows (CWL v1.3)
4. Executes workflows via Apache Airflow 3

### 1.2 Core Standards

| Standard | Usage |
|----------|-------|
| **CWL v1.3** | Internal workflow description format |
| **ISA-JSON** | Study design serialization (Investigation -> Study -> Assay) |
| **SPARC SDS** | Dataset structure for all data objects |
| **Apache Airflow 3** | Workflow execution engine |

### 1.3 Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Vue 3 + Vue Flow + TypeScript + Tailwind CSS 4 |
| Backend | Python 3.11 + FastAPI |
| AI Engine | Gemini 3 via `google-genai` SDK |
| State Management | Pinia |
| Storage | MinIO (S3-compatible) |
| Execution | Apache Airflow 3.0.6 (LocalExecutor) |
| CWL Runner | cwltool via Docker-in-Docker |
| Database | PostgreSQL 15 |
| Containerization | Docker Compose (9 services) |

---

## 2. Architecture

### 2.1 High-Level Architecture

```
+-------------------------------------------------------------------+
|                        VeriFlow System                              |
+--------------------------------------------------------------------+
|  +--------------+    +------------------+    +-----------------+   |
|  |  Vue 3 UI    |<-->|  FastAPI Backend  |<-->|  Gemini 3 API   |   |
|  |  (Vue Flow)  |    |  (5 API routers) |    |  (3 Agents)     |   |
|  +------+-------+    +--------+---------+    +-----------------+   |
|         |                     |                                     |
|         | REST API            | Services Layer                      |
|         v                     v                                     |
|  +--------------+    +------------------+                           |
|  |   Console    |    |   PostgreSQL 15  |                           |
|  |   Logs       |    |   (Sessions)     |                           |
|  +--------------+    +------------------+                           |
|                               |                                     |
|         +---------------------+---------------------+              |
|         v                     v                     v              |
|  +--------------+    +------------------+    +-------------+       |
|  |    MinIO     |    |  Airflow 3.0.6   |    |  Docker-in  |       |
|  |  (4 buckets) |<-->|  (API + Sched)   |<-->|  -Docker    |       |
|  +--------------+    +------------------+    +-------------+       |
|                                                     |              |
|                                              +------+------+      |
|                                              | CWL Runner  |      |
|                                              | (cwltool)   |      |
|                                              +-------------+      |
+--------------------------------------------------------------------+
```

### 2.2 Docker Compose Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `backend` | python:3.11-slim | 8000 | FastAPI backend with hot-reload |
| `frontend` | node:20 / nginx | 3000 | Vue 3 SPA served via nginx |
| `postgres` | postgres:15 | 5432 | Primary database |
| `minio` | minio/minio | 9000, 9001 | S3-compatible object storage |
| `minio-init` | minio/mc | - | Bucket initialization |
| `airflow-apiserver` | custom | 8080 | Airflow 3.0.6 API server |
| `airflow-scheduler` | custom | - | Airflow task scheduler |
| `dind` | docker:dind | - | Docker-in-Docker for CWL execution |
| `cwl` | custom | - | CWL runner (cwltool) |

### 2.3 Request Flow

```
User uploads PDF
       |
       v
+------------------------+
| POST /publications/upload |
+-----------+------------+
            v
+------------------------+
|  Scholar Agent         | --> Extracts ISA hierarchy (Gemini 3)
|  (PDF upload +         | --> Generates confidence scores
|   structured output +  | --> Grounding with Google Search
|   thinking: HIGH)      |
+-----------+------------+
            v
+------------------------+
| User selects Assay     |
+-----------+------------+
            v
+------------------------+
|  Engineer Agent        | --> Generates CWL workflow (Gemini 3)
|  (structured output +  | --> Creates Vue Flow graph
|   thinking: HIGH +     | --> Iterative think-act-observe
|   thought signatures)  |
+-----------+------------+
            v
+------------------------+
|  Reviewer Agent        | --> Validates CWL syntax (Gemini 3)
|  (structured output +  | --> Checks data formats
|   thinking: MEDIUM +   | --> Translates errors
|   multi-turn)          |
+-----------+------------+
            v
+------------------------+
| CWL -> Airflow DAG     | --> Converts to DAG
+-----------+------------+
            v
+------------------------+
| Airflow 3 Executor     | --> Runs via Docker-in-Docker
+-----------+------------+
            v
+------------------------+
| Results stored in SDS  | --> MinIO `process` bucket
+------------------------+
```

---

## 3. Data Structures

### 3.1 Pydantic Schemas (Gemini 3 Structured Output)

All agent responses use Pydantic models as `response_schema` for Gemini 3's structured output feature, ensuring type-safe, validated JSON responses.

```python
# Scholar Agent Schema
class AnalysisResult(BaseModel):
    thought_process: str          # Step-by-step reasoning trace
    investigation: Investigation  # ISA hierarchy
    confidence_scores: List[Metric]
    identified_tools: List[Tool]
    identified_models: List[str]
    identified_measurements: List[str]

# Engineer Agent Schema
class WorkflowResult(BaseModel):
    thought_process: str
    workflow_cwl: str             # CWL v1.3 YAML
    tool_cwls: Dict[str, str]
    dockerfiles: Dict[str, str]
    adapters: List[Adapter]
    nodes: List[GraphNode]        # Vue Flow graph nodes
    edges: List[GraphEdge]        # Vue Flow graph edges

# Reviewer Agent Schema
class ValidationResult(BaseModel):
    thought_process: str
    passed: bool
    issues: List[ValidationIssue]
    summary: str

# Error Translation Schema
class ErrorTranslationResult(BaseModel):
    thought_process: str
    translations: List[TranslatedError]
```

### 3.2 ISA-JSON Schema

Standard ISA-JSON format (Investigation -> Study -> Assay):

```typescript
interface Investigation {
  identifier: string;
  title: string;
  description: string;
  studies: Study[];
}

interface Study {
  identifier: string;
  title: string;
  description: string;
  assays: Assay[];
}

interface Assay {
  identifier?: string;
  filename: string;
  measurementType: { term: string };
  technologyType: { term: string };
}
```

### 3.3 Confidence Scores

Stored separately from ISA-JSON (cannot modify the standard):

```typescript
interface ConfidenceScores {
  upload_id: string;
  generated_at: string;  // ISO 8601
  scores: {
    [property_id: string]: {
      value: number;       // 0-100 percentage
      source_page?: number;
      source_text?: string;
    };
  };
}
```

### 3.4 CWL Workflow Schema

Target: **CWL v1.3**:

```yaml
cwlVersion: v1.3
class: Workflow

inputs:
  input_measurements:
    type: Directory
    doc: "SDS primary folder containing subject data"

outputs:
  derived_measurements:
    type: Directory
    outputSource: segmentation/output_dir

steps:
  preprocessing:
    run: tools/dicom-to-nifti.cwl
    in:
      input_dir: input_measurements
    out: [output_dir]

  segmentation:
    run: tools/unet-segmentation.cwl
    in:
      input_dir: preprocessing/output_dir
    out: [output_dir]
```

### 3.5 Vue Flow Graph Schema

```typescript
interface WorkflowGraph {
  nodes: VueFlowNode[];
  edges: VueFlowEdge[];
}

interface VueFlowNode {
  id: string;
  type: "measurement" | "tool" | "model";
  position: { x: number; y: number };  // Auto-layout via dagre
  data: {
    label: string;
    status?: "pending" | "running" | "completed" | "error";
    confidence?: number;
    inputs?: PortDefinition[];
    outputs?: PortDefinition[];
  };
}

interface VueFlowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}
```

---

## 4. Agent System

### 4.1 Agent Overview

| Agent | Model | Thinking Level | Responsibilities |
|-------|-------|----------------|------------------|
| **Scholar** | gemini-3-pro-preview | HIGH (24576) | PDF parsing, ISA extraction, confidence scoring |
| **Engineer** | gemini-3-pro-preview | HIGH (24576) | CWL generation, Dockerfiles, graph layout |
| **Reviewer** | gemini-3-flash-preview | MEDIUM (8192) | Validation, error translation, auto-fix |

### 4.2 Agent Configuration

Agents are configured via `config.yaml` with model aliases and thinking levels:

```yaml
models:
  gemini-3-pro:
    api_model_name: "gemini-3-pro-preview"
    temperature: 1.0
    top_p: 0.95
    max_output_tokens: 8192

  gemini-3-flash:
    api_model_name: "gemini-3-flash-preview"
    temperature: 1.0
    top_p: 0.95
    max_output_tokens: 8192

agents:
  scholar:
    default_model: "gemini-3-pro"
    thinking_level: "HIGH"
  engineer:
    default_model: "gemini-3-pro"
    thinking_level: "HIGH"
  reviewer:
    default_model: "gemini-3-flash"
    thinking_level: "MEDIUM"
```

Prompts are managed via `prompts.yaml` with versioned templates per agent.

### 4.3 Scholar Agent

**Capabilities:**
- Native PDF upload for multimodal analysis
- Pydantic structured output (`AnalysisResult` schema)
- Grounding with Google Search for tool/model verification
- Thinking level: HIGH for deep scientific reasoning
- Agentic Vision mode (page image extraction via PyMuPDF)

**Methods:**
- `analyze_publication()` - Full PDF analysis with structured output + grounding
- `analyze_with_vision()` - Enhanced analysis using page images for diagram extraction

### 4.4 Engineer Agent

**Capabilities:**
- Pydantic structured output (`WorkflowResult` schema)
- Thinking level: HIGH for complex CWL generation
- Iterative think-act-observe via `generate_workflow_agentic()`
- Thought signature preservation across multi-turn iterations

**Methods:**
- `generate_workflow()` - Single-shot CWL generation
- `generate_workflow_agentic()` - Iterative generation with validation loop (max 3 iterations)
- `_quick_validate_cwl()` - Local CWL syntax validation

### 4.5 Reviewer Agent

**Capabilities:**
- Pydantic structured output (`ValidationResult`, `ErrorTranslationResult`)
- Thinking level: MEDIUM for validation, LOW for error translation
- Multi-turn validation with thought signature preservation
- CWL syntax validation (cwltool or fallback)
- Type compatibility checking
- Dependency resolution

**Methods:**
- `validate_workflow()` - Combined local + semantic validation
- `validate_and_fix()` - Iterative validation with thought signatures
- `suggest_fixes()` - Auto-fix suggestions for validation issues
- `_translate_errors()` - Technical to user-friendly error translation

---

## 5. Gemini 3 Integration

### 5.1 SDK

VeriFlow uses the `google-genai` Python SDK (not the legacy `google-generativeai` package) for all Gemini 3 interactions.

```python
from google import genai
from google.genai import types
```

### 5.2 Gemini 3 Features Used

| Feature | How Used |
|---------|----------|
| **Pydantic Structured Output** | All agents use Pydantic `BaseModel` subclasses as `response_schema` for type-safe JSON responses |
| **Thinking Level Control** | `ThinkingConfig(thinking_budget=N, include_thoughts=True)` - HIGH (24576), MEDIUM (8192), LOW (2048) |
| **Grounding with Google Search** | Scholar Agent verifies tool names and model references against the web |
| **Native PDF Upload** | Multimodal file analysis via `client.files.upload()` for publication ingestion |
| **Thought Signature Preservation** | Multi-turn reasoning via `types.Part(thought=True, text=sig)` for iterative workflows |
| **Agentic Vision** | Page image extraction with PyMuPDF for visual analysis of methodology diagrams |
| **Agentic Function Calling** | Think-Act-Observe loops for iterative CWL generation with validation feedback |

### 5.3 GeminiClient

Central client (`app/services/gemini_client.py`) with three methods:

```python
class GeminiClient:
    model_name = "gemini-3-flash-preview"

    def analyze_file(self, file_path, prompt, ..., response_schema, thinking_level, enable_grounding):
        """Native PDF upload + structured output + thinking + grounding + caching"""

    def generate_text(self, prompt, ..., response_schema, thinking_level, enable_grounding):
        """Text-only structured generation for Engineer and Reviewer"""

    def generate_with_history(self, messages, ..., response_schema, thinking_level):
        """Multi-turn with thought signature preservation"""
```

### 5.4 Thought Signature Preservation

For multi-turn agent loops (Engineer agentic generation, Reviewer validate-and-fix), thought signatures are extracted from model responses and re-injected in subsequent turns:

```python
# Extract from response
for part in response.candidates[0].content.parts:
    if hasattr(part, "thought") and part.thought:
        thought_signatures.append(part.text)

# Re-inject in next turn
parts = [types.Part(thought=True, text=sig) for sig in thought_sigs]
parts.append(types.Part(text=content))
contents.append(types.Content(role="model", parts=parts))
```

### 5.5 Local Caching

`GeminiClient.analyze_file()` supports local file-based caching keyed on `model_name + file_hash + prompt_hash` to avoid redundant API calls during development.

---

## 6. API Specification

### 6.1 Base Configuration

```
Base URL: /api/v1
Content-Type: application/json
Docs: /docs (Swagger UI), /redoc (ReDoc)
Health: /health
```

### 6.2 API Routers

| Router | Prefix | Purpose |
|--------|--------|---------|
| `publications` | `/api/v1` | PDF upload, study design, examples |
| `workflows` | `/api/v1` | Workflow assembly, save, retrieve |
| `executions` | `/api/v1` | Execution management, status, results |
| `catalogue` | `/api/v1` | Data object catalogue |
| `settings` | `/api/v1` | Application settings |

### 6.3 Key Endpoints

#### Upload Publication
```http
POST /api/v1/publications/upload
Content-Type: multipart/form-data

Request:
  file: <PDF binary>
  context_file?: <text file>

Response: 200 OK
{
  "upload_id": "pub_abc123",
  "filename": "paper.pdf",
  "status": "processing"
}
```

#### Load Pre-configured Example
```http
POST /api/v1/publications/load-example
{
  "example_name": "mama-mia"
}

Response: 200 OK
{
  "upload_id": "example_mama-mia_...",
  "filename": "mama-mia",
  "status": "completed",
  "message": "Pre-loaded example"
}
```

#### Get Study Design
```http
GET /api/v1/study-design/{upload_id}

Response: 200 OK
{
  "upload_id": "pub_abc123",
  "status": "completed",
  "hierarchy": { "investigation": {...} },
  "confidence_scores": {...}
}
```

#### Assemble Workflow
```http
POST /api/v1/workflows/assemble
{
  "assay_id": "assay_1",
  "upload_id": "pub_abc123"
}

Response: 200 OK
{
  "workflow_id": "wf_789",
  "graph": { "nodes": [...], "edges": [...] }
}
```

#### Run Workflow
```http
POST /api/v1/executions
{
  "workflow_id": "wf_789"
}

Response: 202 Accepted
{
  "execution_id": "exec_456",
  "status": "queued"
}
```

#### Get Execution Status
```http
GET /api/v1/executions/{execution_id}

Response: 200 OK
{
  "execution_id": "exec_456",
  "status": "running",
  "overall_progress": 45,
  "nodes": {...}
}
```

#### Export Results (SDS ZIP)
```http
GET /api/v1/executions/{execution_id}/export

Response: 200 OK (application/zip)
```

#### Real-time Logs (WebSocket)
```
WebSocket /ws/logs

Messages (JSON):
{
  "timestamp": "2026-02-09T12:00:00Z",
  "level": "INFO",
  "message": "Node preprocessing completed",
  "node_id": "step_1",
  "agent": "engineer"
}
```

---

## 7. Frontend Specification

### 7.1 Technology Stack

| Library | Version | Purpose |
|---------|---------|---------|
| Vue | 3.5+ | UI Framework |
| Vue Flow | 1.41+ | Workflow graph visualization |
| Pinia | 2.2+ | State management |
| TypeScript | 5.6+ | Type safety |
| Tailwind CSS | 4.0+ | Styling |
| Vite | 6.0+ | Build tool |
| dagre | 0.8.5 | Graph auto-layout |
| lucide-vue-next | 0.468+ | Icons |
| axios | 1.13+ | HTTP client |

### 7.2 Component Hierarchy

```
App.vue
+-- LandingPageOverlay.vue
+-- Header (inline)
|   +-- ConfigurationPanel.vue
+-- LeftPanel/
|   +-- ResizablePanel.vue
|       +-- UploadModule.vue
|   +-- ResizablePanel.vue (conditional)
|       +-- StudyDesignModule.vue
|           +-- AdditionalInfoModal.vue
+-- CenterPanel/
|   +-- WorkflowAssemblerModule.vue
|       +-- GraphNode.vue (custom Vue Flow node)
|       +-- ConnectionLine.vue (custom Vue Flow edge)
|       +-- DataObjectCatalogue.vue
|       +-- ViewerPanel.vue
+-- RightPanel/
|   +-- CollapsibleHorizontalPanel.vue
|       +-- DatasetNavigationModule.vue
|           +-- FileTreeNode.vue
+-- BottomPanel/
    +-- ConsoleModule.vue
    +-- ConsoleInput.vue
```

### 7.3 State Management (Pinia)

Single store at `stores/workflow.ts`:

```typescript
// Upload state
uploadId, uploadedPdfUrl, hasUploadedFiles

// Study design state
hierarchy, confidenceScores, selectedAssay

// Workflow state
workflowId, nodes, edges, isAssembled, selectedNode, selectedDatasetId

// Execution state
executionId, isWorkflowRunning, nodeStatuses, logs

// UI state
isLeftPanelCollapsed, isRightPanelCollapsed, isConsoleCollapsed
consoleHeight, viewerPdfUrl, isViewerVisible

// Loading state
isLoading, loadingMessage, error
```

**Key Actions:**
- `uploadPublication()` - Upload PDF and trigger study design fetch
- `loadExample()` - Load pre-configured MAMA-MIA demo
- `fetchStudyDesignFromApi()` - Fetch ISA hierarchy from backend
- `assembleWorkflow()` - Request workflow assembly from AI agents
- `runWorkflow()` - Start workflow execution
- `exportResults()` - Download SDS ZIP export

### 7.4 Layout

Four-panel responsive layout:
- **Left Panel**: Upload + Study Design (resizable, collapsible)
- **Center Panel**: Workflow graph canvas (Vue Flow) with data catalogue and viewer
- **Right Panel**: Results visualization and export (collapsible)
- **Bottom Panel**: Console with resizable height and agent log streaming

### 7.5 Vue Flow Integration

Auto-layout using dagre (left-to-right):

```typescript
import dagre from 'dagre';

function getLayoutedElements(nodes, edges, direction = 'LR') {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: direction, nodesep: 50, ranksep: 150 });
  // ... layout calculation
}
```

Custom node types: `measurement`, `tool`, `model` with status-based styling.

---

## 8. Execution Engine

### 8.1 Airflow 3 Configuration

VeriFlow uses Apache Airflow 3.0.6 with:
- **Executor**: LocalExecutor
- **Auth**: FabAuthManager + basic_auth
- **API**: REST API with session + basic_auth backends
- **CWL execution**: Via Docker-in-Docker (dind service)

### 8.2 Services

| Service | Role |
|---------|------|
| `CWLParser` | Parse CWL v1.3 YAML into structured workflow/tool models |
| `DAGGenerator` | Convert CWL workflows to Airflow DAG Python files |
| `DockerBuilder` | Generate Dockerfiles from CWL tool requirements |
| `ExecutionEngine` | Orchestrate workflow execution lifecycle |
| `AirflowClient` | HTTP client for Airflow 3 REST API |
| `SDSExporter` | Export execution results as SPARC SDS ZIP |

### 8.3 CWL Parser

Parses CWL v1.3 workflows and tools:
- Validates `cwlVersion` and `class`
- Extracts inputs/outputs (dict and list formats)
- Resolves step dependencies
- Topological sort for execution order
- Docker requirement extraction

### 8.4 DAG Generator

Converts parsed CWL to Airflow DAGs:
- Maps CWL `CommandLineTool` -> `DockerOperator`
- Generates dependency chains
- Creates Python DAG files in the dags directory

### 8.5 SDS Export

Exports execution results as SPARC SDS compliant ZIP:
- `dataset_description.json`
- `manifest.xlsx` / `manifest.csv`
- Provenance tracking with derivation links
- Output files organized by execution step

---

## 9. Storage System

### 9.1 MinIO Bucket Structure

```
MinIO
+-- measurements/         # Primary measurement datasets (SDS)
|   +-- mama-mia/
|       +-- primary/
|       +-- manifest.xlsx
|       +-- dataset_description.json
+-- workflow/             # Workflow definitions (SDS)
|   +-- wf_789/
|       +-- primary/
|           +-- workflow.cwl
+-- workflow-tool/        # Tool definitions (SDS)
|   +-- dicom-to-nifti/
|       +-- code/
|       +-- Dockerfile
|       +-- tool.cwl
+-- process/              # Execution outputs (Derived SDS)
    +-- exec_456/
        +-- derivative/
        +-- manifest.xlsx
        +-- provenance.json
```

Buckets are auto-created by the `minio-init` service on startup.

---

## 10. Testing

### 10.1 Backend Tests (pytest)

**163 tests** across 19 test files:

| Category | Files | Tests |
|----------|-------|-------|
| Agent tests | `test_scholar.py`, `test_engineer.py`, `test_reviewer.py` | ~30 |
| Service tests | `test_gemini_client.py`, `test_cwl_parser.py`, `test_dag_generator.py`, `test_docker_builder.py`, `test_sds_exporter.py`, `test_execution_engine.py`, `test_airflow_client.py`, `test_minio_service.py`, `test_config.py`, `test_prompt_manager.py` | ~100 |
| API tests | `test_api_health.py`, `test_api_publications.py`, `test_api_workflows.py`, `test_api_executions.py` | ~20 |
| Fixtures | `conftest.py` | - |

**Run:**
```bash
# Local
cd backend && python -m pytest tests/ -v

# Docker
docker compose run --rm backend pytest tests/ -v
```

### 10.2 Frontend Tests (Vitest)

**6 tests** across 2 test files:
- `stores/__tests__/workflow.spec.ts` - Pinia store tests
- `components/modules/__tests__/UploadModule.spec.ts` - Component tests

**Run:**
```bash
cd frontend && npx vitest run
```

### 10.3 Test Guidelines

- **Unit tests**: Mock external clients (Gemini API, MinIO). Test real app functions.
- **Integration tests**: No mock classes/methods. Use real credentials when applicable.
- **Docker compatibility**: `conftest.py` conditionally mocks `google-genai` SDK when not installed.

---

## 11. Error Handling

### 11.1 Error Categories

```typescript
enum ErrorCategory {
  SCHOLAR_EXTRACTION_FAILED = "scholar_extraction_failed",
  ENGINEER_CWL_GENERATION_FAILED = "engineer_cwl_failed",
  REVIEWER_VALIDATION_FAILED = "reviewer_validation_failed",
  AIRFLOW_CONNECTION_FAILED = "airflow_connection_failed",
  DAG_TRIGGER_FAILED = "dag_trigger_failed",
  TOOL_EXECUTION_FAILED = "tool_execution_failed",
  MINIO_UPLOAD_FAILED = "minio_upload_failed",
  INVALID_PDF = "invalid_pdf",
  UNSUPPORTED_FORMAT = "unsupported_format",
  MISSING_DEPENDENCIES = "missing_dependencies"
}
```

### 11.2 Recovery Flow

The Reviewer Agent provides error translation (Gemini 3 with `ErrorTranslationResult` schema) and auto-fix suggestions:

```
Error Detected
      |
      v
+-------------------+
| Reviewer Agent    |
| (Gemini 3 Flash)  |
| thinking: MEDIUM  |
+--------+----------+
         |
    +----+----+
    v         v
+--------+ +------------+
|Auto-fix| |Translate   |
|possible| |to user msg |
+---+----+ +-----+------+
    |             |
    v             v
+--------+  +----------+
| Apply  |  | Show to  |
| fix    |  | user     |
+--------+  +----------+
```

---

## Appendix A: Docker Compose Configuration

See `docker-compose.yml` for the full 9-service configuration:

```yaml
services:
  dind:          # Docker-in-Docker for CWL execution
  backend:       # FastAPI (port 8000, hot-reload in dev)
  frontend:      # Vue 3 via nginx (port 3000)
  postgres:      # PostgreSQL 15 (port 5432)
  minio:         # MinIO object storage (ports 9000, 9001)
  minio-init:    # Bucket initialization
  airflow-apiserver:   # Airflow 3.0.6 API (port 8080)
  airflow-scheduler:   # Airflow task scheduler
  cwl:           # CWL runner (cwltool)
```

**Environment Variables** (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google AI Studio API key (required) |
| `POSTGRES_USER/PASSWORD/DB` | PostgreSQL credentials |
| `MINIO_ACCESS_KEY/SECRET_KEY` | MinIO credentials |
| `AIRFLOW_USERNAME/PASSWORD` | Airflow credentials |
| `AIRFLOW_FERNET_KEY` | Airflow encryption key |

---

## Appendix B: Database Schema

```sql
CREATE TABLE agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    scholar_extraction_complete BOOLEAN DEFAULT FALSE,
    isa_json_path VARCHAR(500),
    confidence_scores_path VARCHAR(500),
    context_used TEXT,
    workflow_id VARCHAR(255),
    cwl_path VARCHAR(500),
    tools_generated JSONB DEFAULT '[]',
    adapters_generated JSONB DEFAULT '[]',
    validations_passed BOOLEAN DEFAULT FALSE,
    validation_errors JSONB DEFAULT '[]',
    suggestions JSONB DEFAULT '[]'
);

CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES agent_sessions(session_id),
    agent VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE executions (
    execution_id VARCHAR(255) PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    session_id UUID REFERENCES agent_sessions(session_id),
    dag_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    config JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    results_path VARCHAR(500)
);
```

---

**Document End**

*This specification reflects the current implementation as of 2026-02-09, built for the Gemini 3 Hackathon.*
