# VeriFlow Technical Specification

**Version**: 3.0.0
**Status**: Implementation Specification
**Last Updated**: 2026-02-09
**Target**: Engineers and AI Agents
**Hackathon**: [Gemini 3 Hackathon](https://gemini3.devpost.com/)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [LangGraph Orchestration](#3-langgraph-orchestration)
4. [Data Structures](#4-data-structures)
5. [Agent System](#5-agent-system)
6. [Gemini 3 Integration](#6-gemini-3-integration)
7. [API Specification](#7-api-specification)
8. [Frontend Specification](#8-frontend-specification)
9. [Execution Engine](#9-execution-engine)
10. [Storage System](#10-storage-system)
11. [Testing](#11-testing)
12. [Error Handling](#12-error-handling)

---

## 1. System Overview

### 1.1 Purpose

VeriFlow is an autonomous Research Reliability Engineer that:
1. Ingests scientific publications (PDF)
2. Extracts methodological logic using AI agents powered by Gemini 3
3. Creates verifiable, executable research workflows (CWL v1.3)
4. Validates generated artifacts with a self-healing retry loop
5. Reviews and critiques the final output for scientific correctness
6. Executes workflows via Apache Airflow 3

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
| Orchestration | LangGraph (StateGraph) |
| State Management | Pinia (frontend), AgentState TypedDict (backend) |
| Session Storage | SQLite (`db/veriflow.db`) |
| Object Storage | MinIO (S3-compatible) |
| Execution | Apache Airflow 3.0.6 (LocalExecutor) |
| CWL Runner | cwltool via Docker-in-Docker |
| Database (Airflow) | PostgreSQL 15 |
| Real-time Comms | WebSocket (FastAPI native) |
| Containerization | Docker Compose (10 services) |

---

## 2. Architecture

### 2.1 High-Level Architecture

```
+---------------------------------------------------------------------+
|                         VeriFlow System                               |
+---------------------------------------------------------------------+
|  +--------------+    +-------------------+    +-----------------+    |
|  |  Vue 3 UI    |<-->|  FastAPI Backend   |<-->|  Gemini 3 API   |    |
|  |  (Vue Flow)  |    |  (5 API routers)  |    |  (3 Agents)     |    |
|  +------+-------+    +--------+----------+    +-----------------+    |
|         |                     |                                      |
|         | REST + WebSocket    | LangGraph StateGraph                 |
|         v                     v                                      |
|  +--------------+    +-------------------+                           |
|  |  Console +   |    | SQLite + Logs     |                           |
|  |  SmartRender |    | (Session State)   |                           |
|  +--------------+    +-------------------+                           |
|                               |                                      |
|         +---------------------+---------------------+               |
|         v                     v                     v               |
|  +--------------+    +------------------+    +-------------+        |
|  |    MinIO     |    |  Airflow 3.0.6   |    |  Docker-in  |        |
|  |  (4 buckets) |<-->|  (API + Sched)   |<-->|  -Docker    |        |
|  +--------------+    +------------------+    +-------------+        |
|                                                     |               |
|                                              +------+------+       |
|                                              | CWL Runner  |       |
|                                              | (cwltool)   |       |
|                                              +-------------+       |
+---------------------------------------------------------------------+
```

### 2.2 Docker Compose Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `backend` | python:3.11-slim | 8000 | FastAPI backend with hot-reload |
| `frontend` | node:20 / nginx | 3000 | Vue 3 SPA served via nginx |
| `postgres` | postgres:15 | 5432 | Database for Airflow |
| `minio` | minio/minio | 9000, 9001 | S3-compatible object storage |
| `minio-init` | minio/mc | - | Bucket initialization |
| `airflow-apiserver` | custom | 8080 | Airflow 3.0.6 API server |
| `airflow-scheduler` | custom | - | Airflow task scheduler |
| `dind` | docker:dind | - | Docker-in-Docker for CWL execution |
| `cwl` | custom | - | CWL runner (cwltool) |
| `veriflow-sandbox` | clin864/veriflow-sandbox | - | Sandbox for script execution (PyTorch + nnU-Net) |

### 2.3 Request Flow (LangGraph)

```
User uploads PDF + provides repo path + optional context
       |
       v
+----------------------------+
| POST /api/v1/orchestrate   |
+------------+---------------+
             v
+----------------------------+
|  VeriFlowService           |
|  run_workflow()             |
+------------+---------------+
             v
+======================================+
|        LangGraph StateGraph          |
|                                      |
|  [scholar] --> [engineer] --> [validate]
|                    ^              |
|                    |   Self-Healing Loop
|                    +-- errors? ---+
|                                   |
|                              [reviewer] --> END
+======================================+
             |
             v (WebSocket streaming throughout)
+----------------------------+
|  Vue 3 Frontend            |
|  Real-time Console Output  |
+----------------------------+
```

---

## 3. LangGraph Orchestration

### 3.1 StateGraph Definition

VeriFlow uses LangGraph's `StateGraph` to orchestrate the multi-agent workflow. The graph is defined in `app/graph/workflow.py`:

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)

# 4 Nodes
workflow.add_node("scholar", scholar_node)
workflow.add_node("engineer", engineer_node)
workflow.add_node("validate", validate_node)
workflow.add_node("reviewer", reviewer_node)

# Edges
workflow.add_edge("scholar", "engineer")
workflow.add_edge("engineer", "validate")
workflow.add_conditional_edges("validate", decide_next_step, {
    "engineer": "engineer",   # Retry path
    "reviewer": "reviewer"    # Success or max-retries path
})
workflow.add_edge("reviewer", END)
```

### 3.2 Self-Healing Retry Loop

The `validate` node checks generated artifacts (Dockerfile has `FROM`, CWL has `cwlVersion`). If errors are found and `retry_count < 3`, the graph routes back to `engineer` for regeneration with the error context injected into the prompt. After 3 retries, the graph proceeds to `reviewer` regardless.

```python
def decide_next_step(state: AgentState) -> Literal["engineer", "reviewer"]:
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    MAX_RETRIES = 3
    if errors and retry_count < MAX_RETRIES:
        return "engineer"
    return "reviewer"
```

### 3.3 Plan & Apply Pattern

Users can interact with individual agents via the Chat API, formulate directives, and restart the workflow from any node:

1. **Chat** (`POST /api/v1/chat/{run_id}/{agent_name}`) - Discuss agent output
2. **Apply** (`POST /api/v1/chat/{run_id}/{agent_name}/apply`) - Store directive + restart

Directives are stored per-agent in `agent_directives` and injected into the prompt on restart:

```python
# Dynamic graph entry point
dynamic_graph = create_workflow(entry_point=start_node)
```

### 3.4 Node Implementations

Each node is an async function in `app/graph/nodes.py`:

| Node | Agent | Responsibilities |
|------|-------|------------------|
| `scholar_node` | Scholar | PDF analysis via `GeminiClient.analyze_file()`, ISA-JSON extraction |
| `engineer_node` | Engineer | CWL + Dockerfile generation via `GeminiClient.generate_content()` with repo context |
| `validate_node` | System | Mock validation (Dockerfile has FROM, CWL has cwlVersion) |
| `reviewer_node` | Reviewer | Critique ISA vs generated code alignment via `GeminiClient.generate_content()` |

All nodes:
- Support `agent_directives` for Plan & Apply restarts
- Stream output via WebSocket (`_create_stream_callback`)
- Log execution to `logs/{run_id}/{step_name}.json`

---

## 4. Data Structures

### 4.1 AgentState (LangGraph Shared State)

The central state object passed between all LangGraph nodes:

```python
class AgentState(TypedDict):
    # Metadata
    run_id: Optional[str]

    # Inputs
    pdf_path: str
    repo_path: str
    user_context: Optional[str]       # Global user context

    # Scholar Output
    isa_json: Optional[Dict[str, Any]]

    # Engineer Context & Output
    repo_context: Optional[str]        # Summary of repo files
    generated_code: Optional[Dict[str, str]]  # Keys: 'dockerfile', 'cwl', 'airflow_dag'

    # Validation & Self-Healing
    validation_errors: List[str]
    validation_report: NotRequired[Dict[str, Any]]
    retry_count: int
    client_id: Optional[str]           # WebSocket routing

    # Reviewer Output
    review_decision: Optional[str]     # 'approved' or 'rejected'
    review_feedback: Optional[str]

    # Plan & Apply
    agent_directives: Dict[str, str]   # Per-agent instructions
```

### 4.2 Pydantic Schemas (Gemini 3 Structured Output)

All class-based agent responses use Pydantic models as `response_schema` for Gemini 3's structured output feature:

```python
# Scholar Agent Schema
class AnalysisResult(BaseModel):
    thought_process: str
    investigation: Investigation
    confidence_scores: List[Metric]
    identified_tools: List[Tool]
    identified_models: List[str]
    identified_measurements: List[str]

# Engineer Agent Schema
class WorkflowResult(BaseModel):
    thought_process: str
    workflow_cwl: str
    tool_cwls: Dict[str, str]
    dockerfiles: Dict[str, str]
    adapters: List[Adapter]
    nodes: List[GraphNode]
    edges: List[GraphEdge]

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

### 4.3 ISA-JSON Schema

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

### 4.4 Vue Flow Graph Schema

```typescript
interface VueFlowNode {
  id: string;
  type: "measurement" | "tool" | "model";
  position: { x: number; y: number };
  data: {
    label: string;
    status?: "pending" | "running" | "completed" | "error";
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

## 5. Agent System

### 5.1 Dual Architecture

VeriFlow has two execution paths for agents:

1. **LangGraph Nodes** (`app/graph/nodes.py`) - Primary workflow path. Node functions create `GeminiClient` instances directly, stream via WebSocket, and log to disk.
2. **Class-Based Agents** (`app/agents/`) - Standalone agent classes (`ScholarAgent`, `EngineerAgent`, `ReviewerAgent`) used by individual API endpoints (e.g., `/publications/upload`).

### 5.2 Agent Overview

| Agent | Model | Thinking Level | Responsibilities |
|-------|-------|----------------|------------------|
| **Scholar** | gemini-3-pro-preview | HIGH (24576) | PDF parsing, ISA extraction, confidence scoring |
| **Engineer** | gemini-3-pro-preview | HIGH (24576) | CWL generation, Dockerfiles, graph layout |
| **Reviewer** | gemini-3-flash-preview | MEDIUM (8192) | Validation, error translation, critique |

### 5.3 Agent Configuration

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
    default_prompt_version: "v2_standard"
  engineer:
    default_model: "gemini-3-pro"
    thinking_level: "HIGH"
    default_prompt_version: "v2_standard"
  reviewer:
    default_model: "gemini-3-flash"
    thinking_level: "MEDIUM"
    default_prompt_version: "v2_standard"
```

Prompts are managed via `prompts.yaml` with versioned templates (`v1_standard`, `v2_standard`) per agent.

### 5.4 Scholar Agent

**Class-based** (`app/agents/scholar.py`):
- Native PDF upload for multimodal analysis
- Pydantic structured output (`AnalysisResult` schema)
- Grounding with Google Search for tool/model verification
- Agentic Vision mode (page image extraction via PyMuPDF)

**LangGraph node** (`scholar_node`):
- Calls `GeminiClient.analyze_file()` with the PDF
- Injects `user_context` and `agent_directives` into prompt
- Streams output via WebSocket
- Returns `isa_json` to state

### 5.5 Engineer Agent

**Class-based** (`app/agents/engineer.py`):
- Pydantic structured output (`WorkflowResult` schema)
- Iterative think-act-observe via `generate_workflow_agentic()` (max 3 iterations)
- Thought signature preservation across multi-turn iterations

**LangGraph node** (`engineer_node`):
- Calls `GeminiClient.generate_content()` with ISA-JSON + repo context
- Reads repository files (`_read_repo_context`, max 50KB)
- Injects `validation_errors` from previous attempts for self-healing
- Streams output via WebSocket
- Returns `generated_code` and incremented `retry_count` to state

### 5.6 Reviewer Agent

**Class-based** (`app/agents/reviewer.py`):
- Pydantic structured output (`ValidationResult`, `ErrorTranslationResult`)
- Multi-turn validation with thought signature preservation
- CWL syntax validation (cwltool or fallback)
- Type compatibility checking

**LangGraph node** (`reviewer_node`):
- Calls `GeminiClient.generate_content()` to critique ISA vs generated code
- Derives `review_decision` ("approved" or "rejected") from response
- Streams output via WebSocket
- Returns `review_decision` and `review_feedback` to state

---

## 6. Gemini 3 Integration

### 6.1 SDK

VeriFlow uses the `google-genai` Python SDK for all Gemini 3 interactions:

```python
from google import genai
from google.genai import types
```

### 6.2 Gemini 3 Features Used

| # | Feature | How Used | Agent(s) |
|---|---------|----------|----------|
| 1 | **Pydantic Structured Output** | `response_schema` parameter with `response_mime_type="application/json"` for type-safe JSON responses | All 3 |
| 2 | **Thinking Level Control** | `ThinkingConfig(thinking_budget=N)` configured per agent in `config.yaml` — HIGH (24,576), MEDIUM (8,192), LOW (2,048) | All 3 |
| 3 | **Grounding with Google Search** | `GoogleSearch()` tool verifies tool names and model references during publication analysis | Scholar |
| 4 | **Native PDF Upload** | `types.Part.from_bytes(data=file_data, mime_type="application/pdf")` for multimodal publication ingestion | Scholar |
| 5 | **Thought Signature Preservation** | `_extract_thoughts()` captures reasoning traces from `response.candidates[].content.parts` where `part.thought == True` | All 3 |
| 6 | **Agentic Vision** | Page image extraction via PyMuPDF for visual analysis of methodology diagrams | Scholar |
| 7 | **Async Streaming** | `client.aio.models.generate_content_stream()` for real-time token streaming via WebSocket | All 3 |

### 6.3 GeminiClient

Central client (`app/services/gemini_client.py`) with robust JSON parsing and streaming:

```python
class GeminiClient:
    model_name = "gemini-3.0-flash"  # Default fallback

    async def analyze_file(self, file_path, prompt, model, stream_callback):
        """Native PDF upload via Part.from_bytes + JSON response + streaming"""

    async def generate_content(self, prompt, model, response_schema, stream_callback):
        """Text-only generation with optional structured output + streaming"""

    def _extract_thoughts(self, response) -> List[str]:
        """Extract chain-of-thought from response candidates"""

    def _robust_parse_json(self, text) -> Dict:
        """json_repair-based parsing handles Markdown backticks and malformed JSON"""
```

Key implementation details:
- **json_repair**: Handles Markdown code blocks (```` ```json ````) and malformed JSON from model outputs
- **Async streaming**: Uses `client.aio.models.generate_content_stream()` for real-time WebSocket output
- **Local caching**: File-based caching keyed on `model + file_hash + prompt_hash` (configurable, disabled by default)
- **Fallback parsing**: If `response.parsed` is None, falls back to `_robust_parse_json(response.text)`

---

## 7. API Specification

### 7.1 Base Configuration

```
Base URL: /api/v1
Content-Type: application/json
Docs: /docs (Swagger UI), /redoc (ReDoc)
WebSocket: /ws/{client_id}
```

### 7.2 API Routers

| Router | Prefix | Purpose |
|--------|--------|---------|
| `publications` | `/api/v1` | PDF upload, study design extraction |
| `workflows` | `/api/v1` | Workflow assembly, save, retrieve, restart, status |
| `mamamia_cache` | `/api/v1` | Pre-cached MAMA-MIA demo data |
| `chat` | `/api/v1` | Plan & Apply consultation mode |
| `websockets` | (none) | WebSocket endpoint at `/ws/{client_id}` |

### 7.3 Key Endpoints

#### Orchestrate Full Workflow
```http
POST /api/v1/orchestrate
{
  "pdf_path": "/path/to/paper.pdf",
  "repo_path": "/path/to/repo",
  "user_context": "Focus on the DICOM-to-NIfTI preprocessing pipeline",
  "client_id": "client_abc123"
}

Response: 200 OK
{
  "status": "completed",
  "message": "Workflow run run_abc123 finished.",
  "result": { "run_id": "run_abc123" }
}
```

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

#### MAMA-MIA Cache (Demo)
```http
GET /api/v1/mama-mia-cache?client_id=client_abc123

Response: 200 OK
{
  "status": "completed",
  "message": "MAMA-MIA cached data loaded.",
  "result": {
    "isa_json": {...},
    "generated_code": {},
    "review_decision": "approved"
  }
}
```
Returns cached Scholar output immediately. If `client_id` is provided, streams all agent outputs (Scholar, Engineer retries, Validation, Reviewer) to the WebSocket console in the background.

#### Chat with Agent (Plan & Apply)
```http
POST /api/v1/chat/{run_id}/{agent_name}
{
  "messages": [
    { "role": "user", "content": "Can you add a DICOM adapter step?" }
  ]
}

Response: 200 OK
{ "reply": "I can add a dcm2niix adapter step between..." }
```

#### Apply Directive and Restart
```http
POST /api/v1/chat/{run_id}/{agent_name}/apply
{
  "directive": "Add a DICOM-to-NIfTI adapter using dcm2niix before segmentation"
}

Response: 200 OK
{ "status": "restarted", "message": "Workflow restarted from engineer with new directive." }
```

#### Restart Workflow from Node
```http
POST /api/v1/workflows/{run_id}/restart?start_node=engineer

Request (optional):
{
  "user_context": "Focus on PyTorch instead of TensorFlow",
  "clear_directives": false
}

Response: 200 OK
{ "status": "accepted", "message": "Workflow restart initiated from 'engineer'", "run_id": "run_abc123" }
```

#### Get Workflow Status
```http
GET /api/v1/workflows/{run_id}/status

Response: 200 OK
{
  "run_id": "run_abc123",
  "status": "completed",
  "review_decision": "approved"
}
```

#### Get Agent Artifact
```http
GET /api/v1/orchestrate/{run_id}/artifacts/{agent_name}

Response: 200 OK
{ ...agent output JSON... }
```

#### WebSocket Real-time Streaming
```
WebSocket /ws/{client_id}

Incoming Messages:
{
  "type": "user_message",
  "content": "What tools are needed?",
  "agent": "scholar"
}

Outgoing Messages:
{
  "type": "agent_stream",
  "agent": "Scholar",
  "chunk": "Based on the methodology..."
}

{
  "type": "status_update",
  "status": "running",
  "message": "Engineer Agent: Generating workflow artifacts..."
}
```

---

## 8. Frontend Specification

### 8.1 Technology Stack

| Library | Version | Purpose |
|---------|---------|---------|
| Vue | 3.5+ | UI Framework |
| Vue Flow | 1.41+ | Workflow graph visualization |
| Pinia | 2.2+ | State management |
| TypeScript | 5.6+ | Type safety |
| Tailwind CSS | 4.0+ | Styling |
| Vite | 6.0+ | Build tool |
| dagre | 0.8.5 | Graph auto-layout |
| markdown-it | latest | Markdown rendering for agent output |
| DOMPurify | latest | HTML sanitization |
| lucide-vue-next | 0.468+ | Icons |
| axios | 1.13+ | HTTP client |

### 8.2 Component Hierarchy

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
    +-- SmartMessageRenderer.vue
```

### 8.3 Key Frontend Services

#### WebSocket Service (`services/websocket.ts`)
Singleton `wsService` managing real-time communication:
- Auto-detects `ws://` or `wss://` based on page protocol
- Routes messages by type: `agent_stream`, `status_update`, `error`
- `connect(clientId)`, `disconnect()`, `on(type, handler)`, `send(data)`

#### SmartMessageRenderer (`components/common/SmartMessageRenderer.vue`)
Intelligent rendering of agent output:
- Detects JSON vs Markdown vs streaming content
- Renders Dockerfiles with syntax highlighting
- Renders CWL files as YAML code blocks
- Handles partial/streaming JSON by extracting artifacts via character-by-character parsing
- Sanitizes HTML via DOMPurify

### 8.4 State Management (Pinia)

**Workflow Store** (`stores/workflow.ts`):
```typescript
// Upload state
uploadId, uploadedPdfUrl, hasUploadedFiles

// Study design state
hierarchy, confidenceScores, selectedAssay

// Workflow state
workflowId, nodes, edges, isAssembled

// Execution state
executionId, isWorkflowRunning, nodeStatuses, logs

// WebSocket
clientId, initWebSocket()

// Loading / Error
isLoading, loadingMessage, error
```

**Key Actions:**
- `initWebSocket()` - Connect WebSocket, register `agent_stream` and `status_update` handlers
- `loadExample()` - Load MAMA-MIA demo via cache endpoint with WebSocket streaming
- `uploadPublication()` - Upload PDF and trigger study design fetch
- `assembleWorkflow()` - Request workflow assembly from AI agents
- `setHierarchyFromOrchestration()` - Map ISA-JSON orchestration result to UI hierarchy
- `runWorkflow()` - Start workflow execution
- `exportResults()` - Download SDS ZIP export

**Console Store** (`stores/console.ts`):
- `appendAgentMessage(agent, chunk)` - Append streaming chunks from WebSocket
- `addSystemMessage(message)` - Add system status messages
- `addMessage({type, agent, content, timestamp})` - Generic message add

### 8.5 Layout

Four-panel responsive layout:
- **Left Panel**: Upload + Study Design (resizable, collapsible)
- **Center Panel**: Workflow graph canvas (Vue Flow) with data catalogue and viewer
- **Right Panel**: Results visualization and export (collapsible)
- **Bottom Panel**: Console with resizable height and real-time agent streaming via SmartMessageRenderer

---

## 9. Execution Engine

### 9.1 Airflow 3 Configuration

VeriFlow uses Apache Airflow 3.0.6 with:
- **Executor**: LocalExecutor
- **Auth**: FabAuthManager + basic_auth
- **API**: REST API with session + basic_auth backends
- **CWL execution**: Via Docker-in-Docker (dind service)

### 9.2 Services

| Service | Role |
|---------|------|
| `CWLParser` | Parse CWL v1.3 YAML into structured workflow/tool models |
| `DAGGenerator` | Convert CWL workflows to Airflow DAG Python files |
| `DockerBuilder` | Generate Dockerfiles from CWL tool requirements |
| `ExecutionEngine` | Orchestrate workflow execution lifecycle |
| `AirflowClient` | HTTP client for Airflow 3 REST API |
| `SDSExporter` | Export execution results as SPARC SDS ZIP |

### 9.3 CWL Parser

Parses CWL v1.3 workflows and tools:
- Validates `cwlVersion` and `class`
- Extracts inputs/outputs (dict and list formats)
- Resolves step dependencies
- Topological sort for execution order
- Docker requirement extraction

### 9.4 DAG Generator

Converts parsed CWL to Airflow DAGs:
- Maps CWL `CommandLineTool` -> `DockerOperator`
- Generates dependency chains
- Creates Python DAG files in the dags directory

### 9.5 SDS Export

Exports execution results as SPARC SDS compliant ZIP:
- `dataset_description.json`
- `manifest.xlsx` / `manifest.csv`
- Provenance tracking with derivation links
- Output files organized by execution step

---

## 10. Storage System

### 10.1 SQLite Session Storage

Primary session storage for LangGraph workflow state:

```
db/veriflow.db
  +-- agent_sessions
      - run_id (PK)
      - scholar_extraction_complete
      - scholar_isa_json_path
      - engineer_workflow_id
      - engineer_cwl_path
      - workflow_complete
      - agent_directives (JSON string)
      - user_context
```

Used by `VeriFlowService` for state persistence and `get_full_state_mock()` for Plan & Apply restarts.

### 10.2 File-Based Logging

Agent outputs are logged to disk per run:

```
logs/{run_id}/
  +-- 1_scholar.json
  +-- 2_engineer_retry_0.json
  +-- 2_engineer_retry_1.json
  +-- 3_validate_retry_1.json
  +-- 3_validate_retry_2.json
  +-- 4_reviewer.json
```

### 10.3 MinIO Bucket Structure

```
MinIO
+-- measurements/         # Primary measurement datasets (SDS)
+-- workflow/             # Workflow definitions (SDS)
+-- workflow-tool/        # Tool definitions (SDS)
+-- process/              # Execution outputs (Derived SDS)
```

Buckets are auto-created by the `minio-init` service on startup.

---

## 11. Testing

### 11.1 Backend Tests (pytest)

| Category | Files | Tests |
|----------|-------|-------|
| Agent tests | `test_scholar.py`, `test_engineer.py`, `test_reviewer.py` | ~30 |
| Service tests | `test_gemini_client.py`, `test_cwl_parser.py`, `test_dag_generator.py`, `test_docker_builder.py`, `test_sds_exporter.py`, `test_execution_engine.py`, `test_airflow_client.py`, `test_minio_service.py`, `test_config.py`, `test_prompt_manager.py` | ~100 |
| API tests | `test_api_health.py`, `test_api_publications.py`, `test_api_workflows.py`, `test_api_executions.py` | ~20 |
| Fixtures | `conftest.py` | - |

**Run:**
```bash
cd backend && python -m pytest tests/ -v
docker compose run --rm backend pytest tests/ -v
```

### 11.2 Frontend Tests (Vitest)

- `stores/__tests__/workflow.spec.ts` - Pinia store tests
- `components/modules/__tests__/UploadModule.spec.ts` - Component tests

**Run:**
```bash
cd frontend && npx vitest run
```

### 11.3 Test Guidelines

- **Unit tests**: Mock external clients (Gemini API). Test real app functions.
- **Integration tests**: No mock classes/methods. Use real credentials when applicable.
- **Docker compatibility**: `conftest.py` conditionally mocks `google-genai` SDK when not installed.

---

## 12. Error Handling

### 12.1 Self-Healing Loop

The LangGraph `validate` node detects errors in generated artifacts. If validation fails:
1. `validation_errors` are written to state
2. `decide_next_step()` routes back to `engineer` (if `retry_count < 3`)
3. Engineer re-generates with errors injected into prompt context
4. After 3 retries, proceeds to Reviewer for final critique

### 12.2 Error Categories

```typescript
enum ErrorCategory {
  SCHOLAR_EXTRACTION_FAILED = "scholar_extraction_failed",
  ENGINEER_CWL_GENERATION_FAILED = "engineer_cwl_failed",
  REVIEWER_VALIDATION_FAILED = "reviewer_validation_failed",
  AIRFLOW_CONNECTION_FAILED = "airflow_connection_failed",
  TOOL_EXECUTION_FAILED = "tool_execution_failed",
  MINIO_UPLOAD_FAILED = "minio_upload_failed",
  INVALID_PDF = "invalid_pdf"
}
```

### 12.3 Recovery Flow

```
Error Detected in validate_node
      |
      v
+-------------------+
|  retry_count < 3? |
+--------+----------+
    Yes  |     No
    v    |     v
+--------+  +------------+
|Re-run  |  |reviewer    |
|engineer|  |node        |
|with    |  |(critique + |
|errors  |  | decision)  |
+--------+  +------------+
```

---

## Appendix A: Docker Compose Configuration

See `docker-compose.yml` for the full 10-service configuration:

```yaml
services:
  dind:          # Docker-in-Docker for CWL execution
  backend:       # FastAPI (port 8000, hot-reload in dev)
  frontend:      # Vue 3 via nginx (port 3000)
  postgres:      # PostgreSQL 15 (port 5432, used by Airflow)
  minio:         # MinIO object storage (ports 9000, 9001)
  minio-init:    # Bucket initialization
  airflow-apiserver:   # Airflow 3.0.6 API (port 8080)
  airflow-scheduler:   # Airflow task scheduler
  cwl:           # CWL runner (cwltool)
  veriflow-sandbox:  # Sandbox for script execution (PyTorch + nnU-Net)
```

**Environment Variables** (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google AI Studio API key (required) |
| `POSTGRES_USER/PASSWORD/DB` | PostgreSQL credentials (Airflow) |
| `MINIO_ACCESS_KEY/SECRET_KEY` | MinIO credentials |
| `AIRFLOW_USERNAME/PASSWORD` | Airflow credentials |
| `AIRFLOW_FERNET_KEY` | Airflow encryption key |

---

## Appendix B: Database Schema

### SQLite (`db/veriflow.db`)

```sql
CREATE TABLE IF NOT EXISTS agent_sessions (
    run_id TEXT PRIMARY KEY,
    scholar_extraction_complete BOOLEAN,
    scholar_isa_json_path TEXT,
    engineer_workflow_id TEXT,
    engineer_cwl_path TEXT,
    workflow_complete BOOLEAN DEFAULT FALSE,
    agent_directives TEXT,          -- JSON string: {"scholar": "...", "engineer": "..."}
    user_context TEXT               -- Global user context
);
```

### PostgreSQL (Airflow-managed)

PostgreSQL 15 is used by Apache Airflow for DAG metadata, task instances, and execution logs. The database is managed by Airflow's `db migrate` command and is not directly accessed by the VeriFlow backend.

---

**Document End**

*This specification reflects the current implementation as of 2026-02-09, built for the Gemini 3 Hackathon.*
