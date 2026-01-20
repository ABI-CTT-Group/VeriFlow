# SPEC: VeriFlow (Hackathon MVP Phase 1)

## 1) Summary
VeriFlow is an AI-powered "Research Reliability Engineer" that ingests a scientific PDF, extracts the experimental workflow, standardizes all entities into SPARC Dataset Structure (SDS) objects, containerizes code into Docker + CWL, assembles an executable workflow, validates inputs, and runs a replication to reproduce results. The MVP focuses on autonomous replication of a segmentation workflow from the paper in `paper/s41597-025-04707-4.pdf` using the paper's own data. The system must be fully dynamic (no hardcoding for the demo), run on a cloud backend, and surface an interactive Vue 3 interface for review, curation, and execution.

## 2) Goals
- End-to-end replication from PDF only: ingest paper -> extract workflow -> build containers -> assemble workflow -> validate inputs -> execute -> view outputs.
- SDS compliance: all required SDS fields must be populated for each dataset and pass schema validation.
- Interoperability: every file has `additional_type` set with MIME type or CWL format identifier.
- Reproducibility: outputs are versioned with provenance links to inputs, tools, models, and workflows.
- User confidence: UI shows workflow topology and metadata cards prior to execution, with manual metadata override.
- Metrics: replication success requires numeric metric match (Dice coefficient) with configurable threshold.

## 3) Scope (Hackathon MVP / Phase 1)
In scope:
- PDF-only ingestion for dynamic workflow extraction.
- Scholar, Engineer, Reviewer services as separate backend services.
- SDS datasets: Investigation, Study, Assay, Tools, Models, Measurements, Workflow.
- Dockerfile + CWL generation for tools.
- Adapter generation for format/type mismatches.
- Validation of SDS + additional_type metadata.
- UI: data object catalog, workflow graph, metadata editor, execution view, results viewer (VolView iframe), logs.
- REST API + OpenAPI spec.
- Async task execution where possible.
- Provenance: store Gemini prompts/responses.
- Output versioning by timestamp + semantic version.

Out of scope for MVP:
- Phases 2+ in Pitch (extensions, user-provided datasets, RAG, DSPy synthesis, etc.).
- Authentication beyond Gemini API key requirement.
- Multi-paper/multi-workflow scaling (design only; implementation supports future extension).

## 4) Users and Personas
- Researcher/Clinician: wants a chat-to-replication workflow, minimal setup, immediate visualization.
- Research Software Engineer: wants container, CWL, metadata, API access, and auditability.

## 5) High-Level Architecture
- UI: Vue 3 web app.
- Backend: Python services (open-source libraries only), deployed on ARDC Nectar Research Cloud.
- Services:
  - Scholar Service: PDF parsing, metadata extraction, ISA/SDS creation.
  - Engineer Service: repo analysis, Docker/CWL generation, adapter synthesis.
  - Reviewer Service: validation, workflow visualization metadata, diagnostics, scoring.
- Storage: Local filesystem (per deployment) for SDS datasets and artifacts; SQLite index for metadata; versioned output folders.
- Async tasks: simple background tasks (no external queue requirement).

## 6) Data Model and SDS Rules
### 6.1 SDS Object Types
- Investigation SDS
- Study SDS
- Assay SDS
- Tool SDS
- Model SDS
- Measurement SDS (input and derived output)
- Workflow SDS (CWL and metadata)

### 6.2 Separation Rules
- Tools, Models, Investigation, Study, Assay are all separate SDS datasets.
- Models are separate from Tools; Model SDS links to Tool SDS.
- ISA objects do not contain subjects/samples.
- Derived outputs are written to a new Measurement SDS with provenance.

### 6.3 Provenance and Linking
Each dataset must capture links:
- Assay -> Study -> Investigation
- Assay -> Workflow SDS
- Assay -> Measurement SDS (input samples)
- Derived Measurement SDS -> wasDerivedFrom (source Measurement SDS)
- Derived Measurement SDS -> Tool SDS + Workflow SDS

### 6.4 File Metadata
- All files in manifests include `additional_type` with MIME type or CWL format identifier (e.g., edam:format_3987).

### 6.5 Workflow Outputs
- Default: store only final outputs as SDS samples.
- User option: "Save Intermediate Results" to persist intermediate datasets.

## 7) Storage Layout and Indexing
- File layout: SDS dataset folders on local storage (per server deployment).
- Metadata index: SQLite DB for fast catalog queries and UI listing.
- Index rebuilt each run; no persistent catalog requirement.
- Output versioning:
  - Folder naming: `run_<timestamp>_v<semver>`
  - Persist provenance metadata and Gemini prompt/response logs for each run.

## 8) Workflow: End-to-End Flow
1) Ingestion
- User uploads PDF.
- Scholar extracts ISA context and workflow nodes.
- Scholar triggers SDS dataset creation via sparc-me.

2) Visualization and Curation
- UI shows workflow graph (Mermaid or compatible JSON graph for interactivity).
- Metadata cards show SDS fields.
- User can edit metadata before execution.

3) Assembly
- Engineer resolves tool repos and data links from paper.
- Engineer infers dependencies, builds Dockerfile, wraps CWL.
- Engineer analyzes `additional_type` and adds adapters if needed.

4) Validation
- Reviewer validates SDS structure and required fields.
- Reviewer validates `additional_type` compatibility for inputs.
- Errors surfaced with actionable guidance.

5) Execution
- Reviewer triggers async workflow run.
- Logs captured and exposed in UI.
- If failures occur, Reviewer translates logs into scientific advice.

6) Output and Review
- Derived outputs saved into new Measurement SDS with provenance.
- Metrics computed (Dice coefficient); configurable threshold determines pass/fail.
- Outputs viewable in embedded VolView iframe.

## 8.1) UX Flow Diagram (Mermaid)
```mermaid
flowchart TD
  A[Landing / Upload PDF] --> B[Ingestion Started]
  B --> C[Scholar Extracts ISA + Workflow]
  C --> D[Create SDS Datasets]
  D --> E[Show Workflow Graph + Metadata Cards]

  E --> F{User Edits Metadata?}
  F -->|Yes| G[Manual Override / Save Metadata]
  F -->|No| H[Continue]

  G --> H[Continue]
  H --> I[Engineer Builds Docker + CWL]
  I --> J[Adapter Generation if Needed]
  J --> K[Reviewer Validates SDS + Types]

  K --> L{Validation Pass?}
  L -->|No| M[Show Errors + Guidance]
  M --> E

  L -->|Yes| N[Execute Workflow (Async)]
  N --> O[Live Logs + Status]

  O --> P[Store Outputs in New Measurement SDS]
  P --> Q[Compute Metrics (Dice, configurable threshold)]
  Q --> R{Meets Threshold?}
  R -->|No| S[Show Failure + Diagnostics]
  R -->|Yes| T[Success]

  T --> U[Results Viewer (VolView iframe)]
  S --> U
```

## 9) Service Responsibilities
### 9.1 Scholar Service
- PDF extraction library: choose suitable Python library (e.g., PyMuPDF) based on accuracy and layout preservation.
- Extract sections: methods, datasets, tools, models, metrics.
- Build ISA objects and SDS datasets via sparc-me.
- Emit extraction confidence and provenance.

### 9.2 Engineer Service
- Resolve repo URLs and data links from paper.
- Infer missing dependencies and versions.
- Build Dockerfile + CWL.
- Generate adapter tools for format or resolution mismatches.
- Store CWL in Workflow SDS.

### 9.3 Reviewer Service
- Validate SDS required fields and schema.
- Validate `additional_type` compatibility.
- Provide UI graph data and catalog.
- Runtime log analysis and recommendations.
- Compute metrics and determine pass/fail.

## 10) API (REST)
- OpenAPI spec required.
- Key endpoints (draft):
  - POST /ingest/pdf
  - GET /datasets
  - GET /datasets/{id}
  - PATCH /datasets/{id} (metadata override)
  - POST /workflow/assemble
  - POST /workflow/execute
  - GET /runs/{run_id}
  - GET /runs/{run_id}/logs
  - GET /runs/{run_id}/metrics

## 11) Async Tasks
- Background execution for long-running steps: PDF parse, container build, execution.
- Task status persisted to SQLite and exposed via API.

## 12) UI Requirements
- Vue 3 app.
- Pages/Views:
  - Upload and ingest
  - Workflow graph (Mermaid/interactive)
  - Catalog of SDS objects (drag/drop)
  - Metadata editor (manual override)
  - Execution console/logs
  - Results viewer (VolView iframe)
- All PRD user actions must be supported.

## 13) Validation and Metrics
- Replication must match paper results via Dice coefficient.
- Threshold configurable in settings (not hardcoded).
- Failures require readable error guidance and next steps.

## 14) Security and Access
- No auth/login for MVP.
- Gemini API key required for use.
- If data links are private/missing, prompt user for credentials or data upload; otherwise surface error.

## 15) Audit and Provenance
- Store Gemini prompts/responses in per-run provenance logs.
- Store exact versions of Dockerfile, CWL, and adapters per run.

## 16) Constraints
- Backend language: Python.
- Open-source libraries only.
- Deploy on ARDC Nectar Research Cloud.
- Local storage for datasets and artifacts.

## 17) Acceptance Criteria
- PDF-only ingestion produces SDS datasets for ISA, tools, models, measurements, workflow.
- All SDS required fields are populated (as provided later).
- Dockerfile + CWL generated and stored in Workflow SDS.
- Workflow graph and metadata cards shown before execution.
- Manual metadata override works and persists.
- Workflow executes asynchronously and produces derived Measurement SDS with provenance.
- Dice coefficient computed; threshold configurable; pass/fail recorded.
- Outputs viewable in VolView iframe.
- REST API and OpenAPI spec available.

## 18) Open Questions / Pending Inputs
- SDS required field checklist (to be provided).
- Exact library choice for PDF extraction.
- Exact metric threshold defaults.

## 19) References
- PRD: `PRD.md`
- Pitch: `Pitch.md`
- Demo paper: `paper/s41597-025-04707-4.pdf`
