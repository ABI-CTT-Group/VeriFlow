# VeriFlow Technical Specification

**Version**: 1.0.0  
**Status**: MVP Specification  
**Last Updated**: 2026-01-29  
**Target**: Engineers and AI Agents

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Data Structures](#3-data-structures)
4. [Agent System](#4-agent-system)
5. [API Specification](#5-api-specification)
6. [Frontend Specification](#6-frontend-specification)
7. [Execution Engine](#7-execution-engine)
8. [Storage System](#8-storage-system)
9. [MVP Constraints](#9-mvp-constraints)
10. [Error Handling](#10-error-handling)

---

## 1. System Overview

### 1.1 Purpose

VeriFlow is an autonomous Research Reliability Engineer that:
1. Ingests scientific publications (PDF)
2. Extracts methodological logic using AI agents
3. Creates verifiable, executable research workflows
4. Executes workflows via Apache Airflow

### 1.2 Core Standards

| Standard | Usage |
|----------|-------|
| **CWL v1.3** | Internal workflow description format |
| **ISA-JSON** | Study design serialization (Investigation → Study → Assay) |
| **SPARC SDS** | Dataset structure for all data objects |
| **Apache Airflow 3** | Workflow execution engine |

### 1.3 Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Vue 3 + Vue Flow + TypeScript |
| Backend | Python FastAPI |
| AI Engine | Gemini 3 API via google-genai SDK |
| Storage | MinIO (S3-compatible) |
| Execution | Apache Airflow 3 (local) |
| Database | PostgreSQL |
| Real-time | WebSocket |

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        VeriFlow System                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────────┐    ┌────────────────┐  │
│  │  Vue 3 UI   │◄──►│  FastAPI Backend │◄──►│  Gemini API    │  │
│  │  (Vue Flow) │    │                 │    │  (3 Agents)    │  │
│  └──────┬──────┘    └────────┬────────┘    └────────────────┘  │
│         │                    │                                  │
│         │ WebSocket          │ REST API                         │
│         ▼                    ▼                                  │
│  ┌─────────────┐    ┌─────────────────┐                        │
│  │   Console   │    │   PostgreSQL    │                        │
│  │   Logs      │    │   (Sessions)    │                        │
│  └─────────────┘    └─────────────────┘                        │
│                              │                                  │
│         ┌────────────────────┼────────────────────┐            │
│         ▼                    ▼                    ▼            │
│  ┌─────────────┐    ┌─────────────────┐    ┌────────────┐      │
│  │    MinIO    │    │  Airflow 3      │    │  Docker    │      │
│  │  (4 buckets)│◄──►│  (Local DAGs)   │◄──►│  Executor  │      │
│  └─────────────┘    └─────────────────┘    └────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Request Flow

```
User uploads PDF
       │
       ▼
┌──────────────────┐
│ POST /publications/upload │
└──────────┬───────┘
           ▼
┌──────────────────┐
│  Scholar Agent   │ ──► Extracts ISA hierarchy
│  (Gemini API)    │ ──► Generates confidence scores
└──────────┬───────┘
           ▼
┌──────────────────┐
│ User selects     │
│ Assay            │
└──────────┬───────┘
           ▼
┌──────────────────┐
│  Engineer Agent  │ ──► Generates CWL workflow
│  (Gemini API)    │ ──► Creates Dockerfiles
└──────────┬───────┘
           ▼
┌──────────────────┐
│  Reviewer Agent  │ ──► Validates CWL syntax
│  (Gemini API)    │ ──► Checks data formats
└──────────┬───────┘
           ▼
┌──────────────────┐
│ CWL → Airflow    │ ──► Converts to DAG
│ Conversion       │
└──────────┬───────┘
           ▼
┌──────────────────┐
│ Airflow Executor │ ──► Runs Docker containers
└──────────┬───────┘
           ▼
┌──────────────────┐
│ Results stored   │ ──► MinIO `process` bucket
│ in SDS format    │
└──────────────────┘
```

---

## 3. Data Structures

### 3.1 SDS Manifest Schema

Physical format: `manifest.xlsx`. Logical schema per row:

```typescript
interface SDSManifestRow {
  // Required fields
  filename: string;      // Relative path from dataset root (e.g., "primary/sub-01/data.nii.gz")
  timestamp: string;     // ISO 8601 datetime, auto-generated
  description: string;   // File description, defaults to "Data file"
  
  // Optional fields
  "file type"?: string;  // Broad category: "text", "image", "data"
  
  // Computed field (auto-detected by sds-converter)
  "additional type"?: string;  // IANA MIME type (e.g., "application/x-nifti")
}
```

### 3.2 ISA-JSON Schema

Standard ISA-JSON format. See: https://isa-specs.readthedocs.io/en/latest/isajson.html

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
  filename: string;
  measurementType: OntologyAnnotation;
  technologyType: OntologyAnnotation;
}
```

### 3.3 Confidence Scores

> **IMPORTANT**: Confidence scores are SEPARATE from ISA-JSON (cannot modify standard).

Store in a dedicated file within the same SDS:

```typescript
// File: confidence_scores.json (stored alongside ISA-JSON)
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

Example:
```json
{
  "upload_id": "pub_123",
  "generated_at": "2026-01-29T10:00:00Z",
  "scores": {
    "inv-title": { "value": 95, "source_page": 1, "source_text": "Automated Tumor Detection..." },
    "study-subjects": { "value": 88, "source_page": 3, "source_text": "384 patients..." }
  }
}
```

### 3.4 CWL Workflow Schema

Target: **CWL v1.3**. Use all four process types as appropriate:

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
      model_weights: model_weights
    out: [output_dir]
```

### 3.5 Vue Flow Graph Schema

Frontend graph representation (converted from CWL):

```typescript
interface WorkflowGraph {
  nodes: VueFlowNode[];
  edges: VueFlowEdge[];
}

interface VueFlowNode {
  id: string;                    // Unique identifier
  type: "measurement" | "tool" | "model";
  position: { x: number; y: number };  // Auto-layout generated
  data: {
    label: string;
    status?: "pending" | "running" | "completed" | "error";
    confidence?: number;         // 0-100
    source_id?: string;          // Reference to PDF citation
    inputs?: PortDefinition[];
    outputs?: PortDefinition[];
  };
}

interface VueFlowEdge {
  id: string;
  source: string;      // Source node ID
  target: string;      // Target node ID
  sourceHandle?: string;
  targetHandle?: string;
}

interface PortDefinition {
  id: string;
  label: string;
  type: string;        // MIME type or CWL type
}
```

### 3.6 Session State Schema

Persisted in PostgreSQL:

```typescript
interface AgentSession {
  session_id: string;           // UUID
  upload_id: string;            // Links to publication
  created_at: string;
  updated_at: string;
  
  // Agent-specific state
  scholar_state: {
    extraction_complete: boolean;
    isa_json_path: string;      // MinIO path
    confidence_scores_path: string;
    context_used: string;       // Context file content
  };
  
  engineer_state: {
    workflow_id: string;
    cwl_path: string;           // MinIO path
    tools_generated: string[];
    adapters_generated: string[];
  };
  
  reviewer_state: {
    validations_passed: boolean;
    validation_errors: string[];
    suggestions: string[];
  };
  
  // Conversation history for Gemini
  conversation_history: Message[];
}

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  agent: "scholar" | "engineer" | "reviewer";
}
```

---

## 4. Agent System

### 4.1 Agent Overview

| Agent | Primary Stage | Responsibilities |
|-------|---------------|------------------|
| **Scholar** | Stage 1 | PDF parsing, ISA extraction, metadata population |
| **Engineer** | Stage 2 | CWL generation, Dockerfile creation, adapter logic |
| **Reviewer** | All Stages | Validation, error translation, user communication |

### 4.2 Agent Invocation

```typescript
// Direct Gemini API calls with session state
interface AgentInvocation {
  agent: "scholar" | "engineer" | "reviewer";
  session_id: string;
  input: {
    type: "pdf_upload" | "assay_selection" | "validation_request" | "error_analysis";
    payload: any;
  };
}

// Example: Scholar invocation
const scholarResponse = await gemini.generate({
  model: "gemini-3-pro",
  systemInstruction: SCHOLAR_SYSTEM_PROMPT,
  history: session.conversation_history,
  contents: [
    { role: "user", parts: [{ text: "Analyze this PDF and extract ISA structure..." }] }
  ]
});
```

### 4.3 Scholar Agent Specification

**System Prompt Requirements:**
```
You are the Scholar Agent for VeriFlow. Your role is to:

1. Parse scientific publications (PDF text, figures, diagrams)
2. Extract the ISA hierarchy:
   - Investigation: Overall research context
   - Study: Experimental design
   - Assay: Specific measurement process
3. Identify data objects:
   - Measurements (input data)
   - Tools (processing software)
   - Models (pre-trained weights)
4. Generate confidence scores (0-100%) for each extracted property
5. Output in ISA-JSON format

When a Context File is provided, use it to supplement ambiguous information.
```

**Input:**
```typescript
interface ScholarInput {
  pdf_url: string;           // MinIO presigned URL
  context_file?: string;     // Optional supplemental notes
}
```

**Output:**
```typescript
interface ScholarOutput {
  isa_json: Investigation;   // ISA-JSON structure
  confidence_scores: ConfidenceScores;
  identified_tools: ToolReference[];
  identified_models: ModelReference[];
  identified_measurements: MeasurementReference[];
}
```

### 4.4 Engineer Agent Specification

**System Prompt Requirements:**
```
You are the Engineer Agent for VeriFlow. Your role is to:

1. Generate CWL v1.3 workflow definitions from extracted methodology
2. Create Dockerfiles for each tool
3. Infer dependencies from:
   - requirements.txt (if available)
   - import statements in code
   - Code timestamps for version inference
4. Generate adapters for type mismatches:
   - Check additional_type (MIME type) compatibility
   - Insert conversion tools (e.g., DICOM → NIfTI)
5. Map SDS inputs/outputs to CWL ports

Use CommandLineTool for executable tools, Workflow for orchestration.
```

**Input:**
```typescript
interface EngineerInput {
  assay_id: string;
  isa_json: Investigation;
  tool_references: ToolReference[];
  model_references: ModelReference[];
}
```

**Output:**
```typescript
interface EngineerOutput {
  workflow_cwl: string;      // CWL v1.3 YAML
  tool_cwls: { [tool_id: string]: string };
  dockerfiles: { [tool_id: string]: string };
  adapters: AdapterDefinition[];
}
```

### 4.5 Reviewer Agent Specification

**System Prompt Requirements:**
```
You are the Reviewer Agent for VeriFlow. Your role is to:

1. Validate CWL syntax and semantics
2. Validate Airflow DAG structure
3. Check data format compatibility:
   - Verify additional_type matches between connected nodes
   - Ensure input data exists and is accessible
4. Check dependencies are resolvable
5. Translate technical errors to user-friendly advice
6. Communicate with user when issues arise

All validations must pass before execution. If validation fails:
- Attempt automatic fix/adapter generation
- Ask user for clarification if needed
- Allow user to abort if unresolvable
```

**Validation Checks:**
```typescript
interface ValidationResult {
  passed: boolean;
  checks: {
    cwl_syntax: { passed: boolean; errors: string[] };
    dag_syntax: { passed: boolean; errors: string[] };
    data_format: { passed: boolean; mismatches: TypeMismatch[] };
    dependencies: { passed: boolean; missing: string[] };
  };
  auto_fixes_applied: string[];
  user_action_required: string[];
}

interface TypeMismatch {
  source_node: string;
  source_type: string;  // e.g., "application/dicom"
  target_node: string;
  target_type: string;  // e.g., "application/x-nifti"
  suggested_adapter: string;
}
```

---

## 5. API Specification

### 5.1 Base Configuration

```
Base URL: /api/v1
Content-Type: application/json
Authentication: JWT Bearer Token (for Airflow integration)
```

### 5.2 Publication Endpoints

#### Upload Publication
```http
POST /publications/upload
Content-Type: multipart/form-data

Request:
  file: <PDF binary>
  context_file?: <text file>  # Optional supplemental notes

Response: 200 OK
{
  "upload_id": "pub_abc123",
  "filename": "mama-mia-paper.pdf",
  "status": "processing",
  "message": "Scholar Agent analyzing...",
  "session_id": "sess_xyz789"
}
```

#### Get Study Design
```http
GET /study-design/{upload_id}

Response: 200 OK
{
  "upload_id": "pub_abc123",
  "status": "completed",
  "hierarchy": {
    "investigation": {
      "identifier": "inv_1",
      "title": "Breast Cancer Segmentation",
      "properties": [
        {
          "id": "inv-title",
          "value": "Breast Cancer Segmentation",
          "source_id": "citation_1",
          "confidence": 95
        }
      ],
      "studies": [...]
    }
  },
  "confidence_scores": {...}
}
```

### 5.3 Workflow Endpoints

#### Assemble Workflow
```http
POST /workflows/assemble
Content-Type: application/json

Request:
{
  "assay_id": "assay_1",
  "upload_id": "pub_abc123"
}

Response: 200 OK
{
  "workflow_id": "wf_789",
  "cwl_path": "workflow/wf_789/workflow.cwl",
  "graph": {
    "nodes": [
      {
        "id": "input-1",
        "type": "measurement",
        "position": { "x": 50, "y": 100 },
        "data": {
          "label": "DCE-MRI Scans",
          "inputs": [],
          "outputs": [{ "id": "out-1", "label": "DICOM", "type": "application/dicom" }]
        }
      },
      {
        "id": "tool-1",
        "type": "tool",
        "position": { "x": 300, "y": 100 },
        "data": {
          "label": "DICOM to NIfTI",
          "inputs": [{ "id": "in-1", "label": "Input", "type": "application/dicom" }],
          "outputs": [{ "id": "out-1", "label": "Output", "type": "application/x-nifti" }]
        }
      }
    ],
    "edges": [
      { "id": "e1", "source": "input-1", "target": "tool-1", "sourceHandle": "out-1", "targetHandle": "in-1" }
    ]
  },
  "validation": {
    "passed": true,
    "checks": {...}
  }
}
```

#### Save Workflow
```http
PUT /workflows/{workflow_id}
Content-Type: application/json

Request:
{
  "graph": {
    "nodes": [...],
    "edges": [...]
  }
}

Response: 200 OK
{
  "workflow_id": "wf_789",
  "updated_at": "2026-01-29T12:00:00Z"
}
```

### 5.4 Execution Endpoints

#### Run Workflow
```http
POST /executions
Content-Type: application/json

Request:
{
  "workflow_id": "wf_789",
  "config": {
    "subjects": [1]  // Subject limit, default 1 for MVP
  }
}

Response: 202 Accepted
{
  "execution_id": "exec_456",
  "status": "queued",
  "dag_id": "veriflow_wf_789_exec_456"
}
```

#### Get Execution Status
```http
GET /executions/{execution_id}

Response: 200 OK
{
  "execution_id": "exec_456",
  "status": "running",
  "overall_progress": 45,
  "nodes": {
    "tool-1": {
      "execution_sub_id": "sub_001",
      "status": "completed",
      "progress": 100
    },
    "tool-2": {
      "execution_sub_id": "sub_002",
      "status": "running",
      "progress": 45
    }
  },
  "logs": [
    {
      "timestamp": "2026-01-29T12:05:00Z",
      "level": "INFO",
      "message": "Starting segmentation step...",
      "node_id": "tool-2"
    }
  ]
}
```

#### Get Results
```http
GET /executions/{execution_id}/results?node_id=tool-2

Response: 200 OK
{
  "execution_id": "exec_456",
  "files": [
    {
      "path": "derivative/sub-001/tumor_mask.nii.gz",
      "node_id": "tool-2",
      "size": 1048576,
      "download_url": "https://minio.local/process/exec_456/..."  // Presigned URL
    }
  ]
}
```

### 5.5 WebSocket Specification

#### Endpoint
```
ws://localhost:8000/ws/logs?execution_id={execution_id}
```

#### Message Types

```typescript
// Server → Client messages
type WebSocketMessage = 
  | AgentStatusMessage
  | NodeStatusMessage
  | LogEntryMessage
  | ExecutionCompleteMessage;

interface AgentStatusMessage {
  type: "agent_status";
  timestamp: string;
  agent: "scholar" | "engineer" | "reviewer";
  status: "idle" | "thinking" | "processing" | "complete" | "error";
  message?: string;
}

interface NodeStatusMessage {
  type: "node_status";
  timestamp: string;
  execution_id: string;
  execution_sub_id: string;
  node_id: string;
  status: "pending" | "running" | "completed" | "error";
  progress: number;  // 0-100
}

interface LogEntryMessage {
  type: "log";
  timestamp: string;
  level: "DEBUG" | "INFO" | "WARNING" | "ERROR";
  message: string;
  node_id?: string;
  agent?: string;
}

interface ExecutionCompleteMessage {
  type: "execution_complete";
  timestamp: string;
  execution_id: string;
  status: "success" | "partial_failure" | "failed";
  results_url: string;
}
```

---

## 6. Frontend Specification

### 6.1 Technology Stack

| Library | Version | Purpose |
|---------|---------|---------|
| Vue | 3.x | UI Framework |
| Vue Flow | latest | Workflow graph visualization |
| Pinia | latest | State management |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 4.x | Styling |

### 6.2 Component Hierarchy

```
App.vue
├── LeftPanel/
│   ├── UploadModule.vue
│   └── StudyDesignModule.vue
├── CenterPanel/
│   ├── WorkflowCanvas.vue (Vue Flow)
│   ├── DataObjectCatalogue.vue
│   └── ViewerPanel.vue
├── RightPanel/
│   └── DatasetNavigationModule.vue
└── BottomPanel/
    └── ConsoleModule.vue
```

### 6.3 State Management (Pinia)

```typescript
// stores/workflow.ts
interface WorkflowState {
  // Upload state
  uploadId: string | null;
  uploadedPdfUrl: string | null;
  hasUploadedFiles: boolean;
  
  // Study design state
  hierarchy: Investigation | null;
  confidenceScores: ConfidenceScores | null;
  selectedAssay: string | null;
  
  // Workflow state
  workflowId: string | null;
  graph: WorkflowGraph;
  isAssembled: boolean;
  selectedNode: string | null;
  selectedDatasetId: string | null;
  
  // Execution state
  executionId: string | null;
  isWorkflowRunning: boolean;
  nodeStatuses: Record<string, NodeStatus>;
  logs: LogEntry[];
  
  // UI state
  isLeftPanelCollapsed: boolean;
  isRightPanelCollapsed: boolean;
  isConsoleCollapsed: boolean;
  consoleHeight: number;
  viewerPdfUrl: string | null;
  isViewerVisible: boolean;
}
```

### 6.4 Vue Flow Integration

```typescript
// components/WorkflowCanvas.vue
import { VueFlow, useVueFlow } from '@vue-flow/core';
import { Background, Controls, MiniMap } from '@vue-flow/additional-components';

// Custom node components
const nodeTypes = {
  measurement: MeasurementNode,
  tool: ToolNode,
  model: ModelNode,
};

// Auto-layout using dagre
import dagre from 'dagre';

function autoLayout(nodes: Node[], edges: Edge[]): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', nodesep: 50, ranksep: 150 });
  
  nodes.forEach(node => {
    g.setNode(node.id, { width: 200, height: 100 });
  });
  
  edges.forEach(edge => {
    g.setEdge(edge.source, edge.target);
  });
  
  dagre.layout(g);
  
  return nodes.map(node => ({
    ...node,
    position: {
      x: g.node(node.id).x - 100,
      y: g.node(node.id).y - 50,
    },
  }));
}
```

### 6.5 Visual Design

```css
/* Node colors */
--measurement-color: #2563eb;  /* Blue */
--tool-color: #9333ea;         /* Purple */
--model-color: #16a34a;        /* Green */

/* Status colors */
--status-pending: #94a3b8;     /* Gray */
--status-running: #2563eb;     /* Blue */
--status-completed: #16a34a;   /* Green */
--status-error: #dc2626;       /* Red */
```

---

## 7. Execution Engine

### 7.1 Airflow Configuration

```python
# airflow.cfg relevant settings
[core]
executor = LocalExecutor
dags_folder = /opt/airflow/dags

[api]
auth_backends = airflow.api.auth.backend.session

[webserver]
expose_config = False
```

### 7.2 CWL to Airflow Conversion

```python
def cwl_to_airflow_dag(cwl_workflow: dict, execution_id: str) -> DAG:
    """
    Convert CWL v1.3 workflow to Airflow DAG.
    
    Mapping:
    - CWL Workflow → Airflow DAG
    - CWL CommandLineTool → DockerOperator
    - CWL inputs → Airflow Variables / XCom
    - CWL scatter → Dynamic Task Mapping
    """
    dag_id = f"veriflow_{execution_id}"
    
    with DAG(
        dag_id=dag_id,
        start_date=datetime.now(),
        catchup=False,
        tags=["veriflow"],
    ) as dag:
        
        for step_id, step in cwl_workflow["steps"].items():
            tool_cwl = load_cwl(step["run"])
            
            task = DockerOperator(
                task_id=step_id,
                image=get_docker_image(tool_cwl),
                command=build_command(tool_cwl, step["in"]),
                mounts=[
                    Mount(source=MINIO_MOUNT, target="/data", type="bind")
                ],
                environment={
                    "INPUT_PATH": resolve_input_path(step["in"]),
                    "OUTPUT_PATH": f"/data/output/{execution_id}/{step_id}",
                },
            )
        
        # Set dependencies based on CWL step connections
        for step_id, step in cwl_workflow["steps"].items():
            for input_ref in step["in"].values():
                if "/" in str(input_ref):  # References another step
                    source_step = input_ref.split("/")[0]
                    dag.get_task(source_step) >> dag.get_task(step_id)
    
    return dag
```

### 7.3 Airflow Authentication

```python
# JWT-based authentication for Airflow API
import requests

class AirflowClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.token = self._get_jwt_token()
    
    def _get_jwt_token(self) -> str:
        response = requests.post(
            f"{self.base_url}/api/v1/security/login",
            json={"username": "veriflow", "password": AIRFLOW_PASSWORD}
        )
        return response.json()["access_token"]
    
    def trigger_dag(self, dag_id: str, conf: dict) -> str:
        response = requests.post(
            f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"conf": conf}
        )
        return response.json()["dag_run_id"]
    
    def get_dag_run_status(self, dag_id: str, dag_run_id: str) -> dict:
        response = requests.get(
            f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.json()
```

### 7.4 Status Polling

Default polling interval: **5 seconds** (Airflow default for task state refresh).

```python
async def poll_execution_status(execution_id: str, websocket: WebSocket):
    """Stream execution status updates via WebSocket."""
    airflow = AirflowClient()
    dag_id = f"veriflow_{execution_id}"
    
    while True:
        status = airflow.get_dag_run_status(dag_id, execution_id)
        
        if status["state"] in ["success", "failed"]:
            await websocket.send_json({
                "type": "execution_complete",
                "execution_id": execution_id,
                "status": status["state"]
            })
            break
        
        # Send node-level updates
        for task in status["task_instances"]:
            await websocket.send_json({
                "type": "node_status",
                "execution_id": execution_id,
                "node_id": task["task_id"],
                "status": task["state"],
                "progress": calculate_progress(task)
            })
        
        await asyncio.sleep(5)  # 5-second polling interval
```

---

## 8. Storage System

### 8.1 MinIO Bucket Structure

```
MinIO
├── measurements/           # Primary measurement datasets (SDS)
│   ├── mama-mia/
│   │   ├── primary/
│   │   │   └── DCE-MRI/
│   │   │       └── sub-001/
│   │   │           └── T1w.nii.gz
│   │   ├── manifest.xlsx
│   │   └── dataset_description.json
│   └── biv-me/
│       └── ...
│
├── workflow/               # Workflow definitions (SDS)
│   ├── wf_789/
│   │   ├── primary/
│   │   │   └── workflow.cwl
│   │   ├── manifest.xlsx
│   │   └── dataset_description.json
│   └── ...
│
├── workflow-tool/          # Tool definitions (SDS)
│   ├── dicom-to-nifti/
│   │   ├── code/
│   │   │   └── convert.py
│   │   ├── Dockerfile
│   │   ├── tool.cwl
│   │   └── manifest.xlsx
│   └── unet-segmentation/
│       └── ...
│
└── process/                # Execution outputs (Derived SDS)
    └── exec_456/
        ├── derivative/
        │   └── segmentation/
        │       └── sub-001/
        │           └── tumor_mask.nii.gz
        ├── manifest.xlsx
        └── provenance.json  # Links to source datasets
```

### 8.2 Presigned URL Generation

```python
from minio import Minio
from datetime import timedelta

minio_client = Minio(
    "localhost:9000",
    access_key="veriflow",
    secret_key=MINIO_SECRET,
    secure=False
)

def get_presigned_download_url(bucket: str, object_name: str, expires: int = 3600) -> str:
    """Generate presigned URL for file download."""
    return minio_client.presigned_get_object(
        bucket,
        object_name,
        expires=timedelta(seconds=expires)
    )

def get_presigned_upload_url(bucket: str, object_name: str) -> str:
    """Generate presigned URL for file upload."""
    return minio_client.presigned_put_object(
        bucket,
        object_name,
        expires=timedelta(hours=1)
    )
```

### 8.3 SDS Export Format

Export as ZIP preserving SDS structure:

```
export_pub_123.zip
├── investigation_sds/
│   ├── dataset_description.json
│   ├── manifest.xlsx
│   └── primary/
│       └── investigation.json  # ISA-JSON
│
├── study_sds/
│   └── ...
│
├── measurements_sds/
│   └── ...  # Only if populated at export time
│
├── workflow_sds/
│   └── ...  # Only if workflow assembled
│
└── process_sds/
    └── ...  # Only if workflow executed
```

---

## 9. MVP Constraints

### 9.1 Scope Boundaries

| Feature | MVP Status | Notes |
|---------|------------|-------|
| MAMA-MIA workflow | ✅ Required | Primary demo case |
| Biv-me workflow | ⭐ Stretch | Secondary example |
| Subject limit | 1 | Default for MVP |
| Save/Resume workflow | ❌ Not in MVP | Export only |
| Load saved state | ❌ Not in MVP | |
| Custom PDF upload | ✅ Supported | |
| Pre-loaded examples | ✅ Required | PDF + Context file |

### 9.2 Pre-loaded Example Configuration

```typescript
interface PreloadedExample {
  id: string;
  name: string;
  pdf_url: string;           // MinIO presigned URL
  context_file_url: string;  // Supplemental notes for Scholar
  ground_truth?: {           // For validation
    isa_json: string;
    workflow_cwl: string;
    expected_outputs: string[];
  };
}

const PRELOADED_EXAMPLES: PreloadedExample[] = [
  {
    id: "mama-mia",
    name: "MAMA-MIA: Breast Cancer Segmentation",
    pdf_url: "measurements/mama-mia/docs/paper.pdf",
    context_file_url: "measurements/mama-mia/docs/context.txt",
    ground_truth: {
      // Used for benchmarking, not displayed
      isa_json: "measurements/mama-mia/ground_truth/investigation.json",
      workflow_cwl: "workflow/mama-mia-gt/workflow.cwl",
      expected_outputs: ["tumor_mask.nii.gz"]
    }
  }
];
```

### 9.3 Context File Format

```
# MAMA-MIA Context File
# Supplemental information for Scholar Agent

## Dataset Information
- Name: MAMA-MIA (Multi-center Annotated Mammary MRI for AI)
- Total Subjects: 1506 patients
- Modality: DCE-MRI (Dynamic Contrast-Enhanced)

## Methodology Details
- Segmentation Model: nnU-Net
- Input Format: NIfTI (converted from DICOM)
- Output: Binary tumor segmentation mask

## Repository Information
- Code Repository: https://github.com/example/mama-mia
- Model Weights: Provided in accompanying weights.zip

## Key Processing Steps
1. DICOM to NIfTI conversion
2. Intensity normalization
3. nnU-Net inference
4. Post-processing (optional)
```

---

## 10. Error Handling

### 10.1 Error Categories

```typescript
enum ErrorCategory {
  // Agent errors
  SCHOLAR_EXTRACTION_FAILED = "scholar_extraction_failed",
  ENGINEER_CWL_GENERATION_FAILED = "engineer_cwl_failed",
  REVIEWER_VALIDATION_FAILED = "reviewer_validation_failed",
  
  // Execution errors
  AIRFLOW_CONNECTION_FAILED = "airflow_connection_failed",
  DAG_TRIGGER_FAILED = "dag_trigger_failed",
  TOOL_EXECUTION_FAILED = "tool_execution_failed",
  
  // Storage errors
  MINIO_UPLOAD_FAILED = "minio_upload_failed",
  MINIO_DOWNLOAD_FAILED = "minio_download_failed",
  
  // Data errors
  INVALID_PDF = "invalid_pdf",
  UNSUPPORTED_FORMAT = "unsupported_format",
  MISSING_DEPENDENCIES = "missing_dependencies"
}
```

### 10.2 Error Response Format

```typescript
interface ErrorResponse {
  error: {
    code: ErrorCategory;
    message: string;           // User-friendly message
    details?: string;          // Technical details
    suggestions?: string[];    // Reviewer Agent suggestions
    recoverable: boolean;
    retry_action?: string;     // Suggested retry endpoint
  };
  session_id?: string;
  timestamp: string;
}
```

### 10.3 Recovery Flow

```
Error Detected
      │
      ▼
┌─────────────────┐
│ Reviewer Agent  │
│ analyzes error  │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│Auto-fix│ │Ask user for│
│possible│ │clarification│
└───┬────┘ └─────┬──────┘
    │            │
    ▼            ▼
┌────────┐ ┌────────────┐
│ Apply  │ │ User input │
│ fix    │ └─────┬──────┘
└───┬────┘       │
    │      ┌─────┴─────┐
    ▼      ▼           ▼
┌──────────────┐ ┌──────────┐
│ Retry step   │ │ Abort    │
└──────────────┘ └──────────┘
```

---

## Appendix A: Docker Compose Configuration

```yaml
version: '3.8'

services:
  veriflow-backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://veriflow:password@postgres:5432/veriflow
      - MINIO_ENDPOINT=minio:9000
      - AIRFLOW_URL=http://airflow-webserver:8080
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - postgres
      - minio
      - airflow-webserver

  veriflow-frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - veriflow-backend

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=veriflow
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=veriflow
    volumes:
      - postgres_data:/var/lib/postgresql/data

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=veriflow
      - MINIO_ROOT_PASSWORD=password
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

  airflow-webserver:
    image: apache/airflow:2.8.0
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql://veriflow:password@postgres:5432/airflow
    volumes:
      - ./dags:/opt/airflow/dags
      - minio_data:/data  # Shared with MinIO for Airflow access
    depends_on:
      - postgres

volumes:
  postgres_data:
  minio_data:
```

---

## Appendix B: Database Schema

```sql
-- Sessions table
CREATE TABLE agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Scholar state
    scholar_extraction_complete BOOLEAN DEFAULT FALSE,
    isa_json_path VARCHAR(500),
    confidence_scores_path VARCHAR(500),
    context_used TEXT,
    
    -- Engineer state
    workflow_id VARCHAR(255),
    cwl_path VARCHAR(500),
    tools_generated JSONB DEFAULT '[]',
    adapters_generated JSONB DEFAULT '[]',
    
    -- Reviewer state
    validations_passed BOOLEAN DEFAULT FALSE,
    validation_errors JSONB DEFAULT '[]',
    suggestions JSONB DEFAULT '[]'
);

-- Conversation history
CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES agent_sessions(session_id),
    agent VARCHAR(20) NOT NULL,  -- scholar, engineer, reviewer
    role VARCHAR(20) NOT NULL,   -- user, assistant, system
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Executions
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

-- Indexes
CREATE INDEX idx_sessions_upload ON agent_sessions(upload_id);
CREATE INDEX idx_history_session ON conversation_history(session_id);
CREATE INDEX idx_executions_workflow ON executions(workflow_id);
```

---

**Document End**

*This specification is designed for engineers and AI agents implementing VeriFlow. For stakeholder-facing documentation, see PRD.md.*
