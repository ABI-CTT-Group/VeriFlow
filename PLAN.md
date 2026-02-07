# VeriFlow MVP Development Plan

**Version**: 1.0.0  
**Created**: 2026-01-29  
**Target**: Hackathon MVP  

---

## Execution Scope

- This PLAN is intended for **AI execution**
- The AI MUST strictly follow all constraints defined in this document
- Any ambiguity must be resolved by asking the developer, not by assumption

## UI Authority Declaration

- The UI located at `planning/UI` is the **authoritative UI definition**
- The AI MUST treat it as immutable ground truth
- The frontend task is a **UI porting task**, not a UI design task

## UI Parity Hard Rule (Global)

### UI Source of Truth Priority Order
When performing any UI porting or parity validation, the following priority MUST be respected:

1. Global CSS / Design System (index.css, theme tokens, CSS variables)
2. Screenshot reference (UI.jpg)
3. Component structure and Tailwind class usage
4. JSX / TSX / Vue SFC markup

Any mismatch in Global CSS MUST be resolved before component-level adjustments.

### Hard Rule
Component-level Tailwind class parity is NOT sufficient to guarantee visual parity.
Global CSS (colors, typography, spacing scale, resets) must be synchronized first.

## Change Policy

- The AI is NOT allowed to:
  - Modify PRD, SPEC, or UI
  - Introduce new features
  - Simplify or redesign UI
- Any required deviation MUST be explicitly reported and justified


## 1. Overview

### 1.1 System Goals

VeriFlow is an autonomous "Research Reliability Engineer" that:
1. Ingests scientific publications (PDF) and extracts methodological logic using AI agents
2. Creates verifiable, executable research workflows in CWL format
3. Executes workflows via Apache Airflow 3 with Docker containers
4. Maintains data interoperability via SPARC Dataset Structure (SDS) and ISA Framework

### 1.2 Non-Goals (MVP)

- Multi-user collaboration features
- Workflow versioning and branching
- Custom PDF upload beyond pre-loaded examples (stretch)
- Save/Resume workflow state persistence
- Phase 4+ features (Extension, User Data, RAG Augmentation scenarios)

### 1.3 Key Assumptions

1. **MAMA-MIA** breast cancer segmentation is the primary demo case
2. **Subject limit**: Default to 1 subject for MVP execution
3. **Local execution**: Airflow runs locally with `LocalExecutor`
4. **Pre-loaded examples**: PDF + Context file provided, not dynamically uploaded
5. **No authentication**: MVP skips user auth for frontend/backend

### 1.4 Open Questions / Ambiguities

| Question | Assumed Resolution |
|----------|-------------------|
| Biv-me workflow inclusion? | Stretch goal only |
| Real Gemini API integration? | Yes, direct API calls with hardcoded prompts |
| CWL validation library? | Use `cwltool --validate` CLI |
| WebSocket vs polling for status? | WebSocket for real-time, with polling fallback |

---

## 2. UI Conversion Contract (CRITICAL)

This project includes a **strict UI porting task**, not UI design or redesign.

### UI Ground Truth
- The UI located at `planning/UI` (React implementation) is the **single source of truth**
- This includes:
  - Layout and panel structure
  - Visual hierarchy and spacing
  - Component boundaries
  - User interactions and behaviors
  - Conditional rendering logic

### Target Requirement
- The frontend MUST be implemented using **Vue 3 (Composition API)**
- The resulting Vue UI MUST be visually and functionally equivalent to the React UI

### Hard Rules
- ❌ DO NOT create new UI components that do not exist in planning/UI
- ❌ DO NOT merge or split components unless explicitly present in React source
- ❌ DO NOT redesign or reinterpret the UI
- ❌ DO NOT simplify layout or components
- ❌ DO NOT introduce new UI patterns
- ❌ DO NOT remove existing UI affordances
- ✅ ONLY translate React components into Vue 3 equivalents

### Acceptance Standard
- Any visual or interaction difference between:
  - `planning/UI` (React)
  - `frontend/src` (Vue)
  is considered a **bug**, not an enhancement

---

## 3. Development Stages

### Stage 1: Infrastructure & Foundation
**Entry Criteria**: Project repository initialized  
**Exit Criteria**: Docker Compose running, all services accessible, database schema applied

### Stage 2: Backend Core APIs
**Entry Criteria**: Stage 1 complete  
**Exit Criteria**: All API endpoints functional with mock data, Pydantic models validated

### Stage 3: Frontend UI Porting (React → Vue 3)
**Entry Criteria**: Stage 2 complete  
**Exit Criteria**: All UI modules implemented, connected to backend APIs

### Stage 4: Agent Integration (Gemini)
**Entry Criteria**: Stage 3 complete  
**Exit Criteria**: Scholar, Engineer, Reviewer agents functional with Gemini API

### Stage 5: Workflow Execution Engine
**Entry Criteria**: Stage 4 complete  
**Exit Criteria**: CWL→Airflow conversion working, Docker execution verified

### Stage 6: End-to-End Integration
**Entry Criteria**: Stage 5 complete  
**Exit Criteria**: MAMA-MIA workflow runs from PDF upload to result visualization

---

## 4. Tasks per Stage

### Stage 1: Infrastructure & Foundation

#### AI Tasks
- [x] Create `docker-compose.yml` with all services (FastAPI, PostgreSQL, MinIO, Airflow)
- [x] Create PostgreSQL database schema (`agent_sessions`, `conversation_history`, `executions`)
- [x] Configure MinIO buckets (`measurements`, `workflow`, `workflow-tool`, `process`)
- [x] Create Airflow DAGs folder structure
- [x] Write environment variable configuration (`.env.example`)
- [x] Create FastAPI project skeleton with routers
- [x] Create Vue 3 project with Vite and Vue Flow

#### Developer Tasks
- [x] Obtain Gemini API key and set `GEMINI_API_KEY` environment variable
- [x] Run `docker-compose up` to verify all services start
- [x] Validate MinIO console accessible at `localhost:9001`
- [x] Validate Airflow web UI accessible at `localhost:8080`

---

### Stage 2: Backend Core APIs

#### AI Tasks
- [x] Implement Pydantic models for all data structures:
  - [x] `SDSManifestRow`
  - [x] `Investigation`, `Study`, `Assay` (ISA-JSON)
  - [x] `ConfidenceScores`
  - [x] `WorkflowGraph`, `VueFlowNode`, `VueFlowEdge`
  - [x] `AgentSession`, `Message`
- [x] Implement Publication API:
  - [x] `POST /publications/upload` - File upload with MinIO storage
  - [x] `GET /study-design/{upload_id}` - Return ISA hierarchy
  - [x] `PUT /study-design/nodes/{node_id}/properties` - Update property
- [x] Implement Workflow API:
  - [x] `POST /workflows/assemble` - Generate graph from assay
  - [x] `GET /workflows/{workflow_id}` - Get workflow state
  - [x] `PUT /workflows/{workflow_id}` - Save workflow
- [x] Implement Catalogue API:
  - [x] `GET /catalogue` - List all data objects
  - [x] `PUT /catalogue/{item_id}` - Update item metadata
- [x] Implement Execution API:
  - [x] `POST /executions` - Trigger workflow run
  - [x] `GET /executions/{execution_id}` - Get execution status
  - [x] `GET /executions/{execution_id}/results` - Get result files
- [x] Implement WebSocket endpoint:
  - [x] `ws://localhost:8000/ws/logs` - Real-time log streaming
- [x] Implement Viewer API:
  - [x] `GET /sources/{source_id}` - Get PDF citation snippet
- [x] Create MinIO service layer for presigned URLs
- [x] Create PostgreSQL service layer for session management

#### Developer Tasks
- [x] Verify API endpoints with Postman/curl
- [x] Confirm database tables created correctly

---

### Stage 3: Frontend UI Porting (React → Vue 3)

The AI MUST complete UI porting and parity validation
BEFORE implementing any additional frontend logic or optimizations

#### Input Reference (Mandatory)
- Source UI: `planning/UI` (React implementation)
- This directory MUST be read and treated as the authoritative reference
- All Vue components MUST correspond 1-to-1 with React components where possible

#### AI Tasks
- [x] Set up Vue 3 + TypeScript + Vite project
- [x] Install dependencies: Vue Flow, Pinia, Tailwind CSS 4, Lucide icons
- [x] Create Pinia store for workflow state:
  - [x] `uploadId`, `uploadedPdfUrl`, `hasUploadedFiles`
  - [x] `hierarchy`, `confidenceScores`, `selectedAssay`
  - [x] `workflowId`, `graph`, `isAssembled`, `selectedNode`
  - [x] `executionId`, `isWorkflowRunning`, `nodeStatuses`, `logs`
  - [x] UI state: panel collapse states, console height
- [x] Implement Left Panel:
  - [x] `UploadModule.vue` - Drag-and-drop file upload
  - [x] `StudyDesignModule.vue` - Tree view with confidence scores
- [x] Implement Center Panel:
  - [x] `WorkflowCanvas.vue` - Vue Flow integration with custom nodes
  - [x] `MeasurementNode.vue` - Blue node with dataset selectors
  - [x] `ToolNode.vue` - Purple node with input/output ports
  - [x] `ModelNode.vue` - Green node with config params
  - [x] `DataObjectCatalogue.vue` - Tree view of data objects
  - [x] `ViewerPanel.vue` - PDF viewer with plugin system
- [x] Implement Right Panel:
  - [x] `DatasetNavigationModule.vue` - File tree viewer
- [x] Implement Bottom Panel:
  - [x] `ConsoleModule.vue` - Real-time logs with resize
- [x] Implement panel resize and collapse functionality
- [x] Implement drag-and-drop between catalogue and canvas
- [x] Implement node connection logic (output→input ports)
- [x] Implement "Run Workflow" button with status updates
- [x] Connect all components to backend APIs

#### Developer Tasks
- [x] Review component visual design matches specifications
- [x] Verify drag-and-drop interactions work correctly

#### UI Parity Validation (Required)

Before Stage 3 can be considered complete, the AI MUST:

- [ ] Enumerate all React components found in `planning/UI`
- [ ] List corresponding Vue components created
- [ ] Confirm parity for each component:
  - Layout structure
  - Props / state mapping
  - User interactions
- [ ] Report any deviation explicitly with justification

Stage 3 is NOT complete until UI parity is verified.

## Stage 3.1 – UI Parity Correction Pass

**Purpose**  
Ensure the Vue 3 implementation is visually and functionally identical to the React UI provided in `planning/UI`.

This stage exists because Stage 3 produced a Vue UI that does not fully match the React reference.
Stage 3 remains logically complete, but UI parity must be explicitly validated and corrected here.



### Ground Truth (STRICT)
The following sources define the canonical UI and must be followed in priority order:

1. React UI source code in `planning/UI`
2. React UI screenshots in `planning/UI/UI.jpg`
3. UI behavior implicitly expressed by React component logic

If any ambiguity exists:
- Screenshots take precedence over inferred layouts
- React behavior takes precedence over Vue implementation convenience



### Rules (NON-NEGOTIABLE)
- This is a **correction pass**, not new UI development.
- No redesign, refactor, optimization, or stylistic interpretation is allowed.
- Vue components must mirror React components one-to-one unless explicitly justified.
- “Visually similar” is insufficient — parity must be exact.
- All existing Vue UI code is assumed incorrect until verified against React.
- No progression to subsequent stages is allowed until parity is confirmed.



### Tasks
### Tasks (AI Tasks)

- [x] Enumerate all React UI components in `planning/UI`
- [x] Map each React component to its corresponding Vue component
- [x] Compare layout structure and component hierarchy
- [x] Compare visual styling using screenshots as ground truth
- [x] Compare state variables and conditional rendering
- [x] Compare all user interactions and side effects
- [x] List all UI mismatches explicitly
- [x] Fix all identified mismatches in Vue components
- [x] Re-verify full parity after fixes
- [x] Create `stage3-ui-parity.md` report
- [x] Update Stage 3.1 task checkboxes in PLAN.md



### Outputs
- `stage3-ui-parity.md` parity report containing:
  - Full React → Vue component mapping
  - Identified discrepancies
  - Applied fixes
  - Remaining issues (if any)
- Updated Vue 3 UI code with confirmed parity



### Exit Criteria
- Every React UI component has a corresponding Vue component.
- No unresolved visual, layout, or interaction differences remain.
- `stage3-ui-parity.md` explicitly confirms full parity.
- Stage 3.1 tasks are fully checked off in PLAN.md.

## Stage 3.2 – UI Visual Refinement Pass

**Objective:**  
Ensure the Vue 3 frontend **visually matches the React UI reference**. Focus on:

- Button sizes, text size, line height  
- Element margins and padding  
- Fonts, colors, borders, backgrounds  
- Icon sizes and positioning  
- Interactive states (hover, active, disabled)

**Reference Inputs:**  
- React UI source: `planning/UI`  
- Screenshot reference: `UI.jpg`

### Tasks

#### AI Tasks
- [x] Compare each Vue component with the corresponding React component and screenshot.
- [x] Identify all visual deviations (font size, button size, spacing, colors, borders, icons, interactive states).
- [x] Correct CSS/Tailwind classes or component styles.
- [x] Ensure hot-reload is working and updates are reflected in the dev server.
- [x] Update `PLAN.md` Stage 3.2 tasks as complete.
- [x] Generate `reports/stage3.2.md` in the Completion Report format.

#### Developer Tasks
- [x] Validate all visual corrections in the browser.
- [x] Confirm interactive behaviors match React UI.
- [x] Sign off Stage 3.2 completion.

---

### Stage 4: Agent Integration (Gemini)

#### AI Tasks
- [x] Create Gemini API client wrapper
- [x] Implement Scholar Agent:
  - [x] System prompt for PDF parsing and ISA extraction
  - [x] PDF text extraction using PyMuPDF
  - [x] ISA-JSON output generation
  - [x] Confidence score generation
- [x] Implement Engineer Agent:
  - [x] System prompt for CWL generation
  - [x] Dependency inference from code
  - [x] Dockerfile generation
  - [x] Adapter generation for type mismatches
- [x] Implement Reviewer Agent:
  - [x] System prompt for validation
  - [x] CWL syntax validation
  - [x] Error translation to user-friendly messages
- [x] Implement session context management
- [x] Store conversation history in PostgreSQL
- [x] Create pre-loaded example configuration:
  - [x] MAMA-MIA PDF and context file
  - [x] Ground truth ISA-JSON for validation

#### Developer Tasks
- [x] Verify Gemini API responses match expected formats
- [x] Test agent prompts produce reasonable outputs

---

### Stage 5: Workflow Execution Engine

#### AI Tasks
- [x] Implement CWL→Airflow DAG conversion:
  - [x] Parse CWL v1.3 workflow YAML
  - [x] Map `CommandLineTool` to `DockerOperator`
  - [x] Handle step dependencies
  - [x] Configure MinIO mounts
- [x] Implement Airflow API client:
  - [x] Session-based authentication
  - [x] DAG trigger
  - [x] Status polling (5-second interval)
  - [x] Log retrieval
- [x] Implement Docker image building:
  - [x] Generate Dockerfiles from tool CWL
  - [x] Build and push to local registry (placeholder for MVP)
- [x] Implement execution status WebSocket streaming
- [x] Implement results storage in MinIO `process` bucket
- [x] Implement provenance linking (wasDerivedFrom)

#### Developer Tasks
- [x] Verify DAGs appear in Airflow UI
- [x] Manually trigger sample DAG to verify Docker execution

---

### Stage 6: End-to-End Integration

#### AI Tasks
- [x] Integrate all components for MAMA-MIA demo flow:
  - [x] Load pre-loaded PDF example (added `/publications/load-example` endpoint)
  - [x] Study design fetch from API with fallback to mock
  - [x] User selects assay (existing functionality)
  - [x] Engineer generates workflow graph (existing functionality)
  - [x] User runs workflow (existing functionality)
  - [x] Results displayed in right panel (existing functionality)
- [x] Implement error handling for all failure modes
  - [x] API error responses with HTTPException
  - [x] Store error state and clearError action
  - [x] User-friendly error messages in console
- [x] Add console logging for all operations
  - [x] Log messages in loadExample action
  - [x] Log messages in fetchStudyDesignFromApi
  - [x] Log messages in exportResults action
- [x] Implement SDS export functionality (ZIP download)
  - [x] Created `export.py` service with manifest, provenance generation
  - [x] Added `/executions/{id}/export` endpoint
  - [x] Export button in DatasetNavigationModule
- [x] Performance optimization and loading states
  - [x] isLoading state in workflow store
  - [x] loadingMessage state for context
  - [x] Loading spinners in UploadModule ("Load Demo" button)
  - [x] Loading spinners in DatasetNavigationModule (export button)
- [x] Dockerize Frontend
  - [x] Create multi-stage Dockerfile (Node.js build + Nginx serve)
  - [x] Create nginx.conf for SPA routing
  - [x] Add frontend service to docker-compose.yml

#### Developer Tasks
- [ ] Complete walkthrough of demo flow
- [ ] Verify results match expected outputs
- [ ] Sign off on MVP completion

---

## 5. Testing Plan per Stage

### Stage 1: Infrastructure Tests

#### Unit Tests
- [ ] Test Docker Compose service health checks
- [ ] Test PostgreSQL connection and schema
- [ ] Test MinIO bucket creation

**Command**: `pytest tests/infrastructure/`

#### Integration Tests
- [ ] Verify services communicate (FastAPI→PostgreSQL, FastAPI→MinIO)

**Command**: `docker-compose up -d && pytest tests/integration/test_services.py`

---

### Stage 2: Backend API Tests

#### Unit Tests
- [ ] Test all Pydantic model validation
- [ ] Test API endpoint handlers with mocked dependencies

**Command**: `pytest tests/backend/unit/`

#### Integration Tests
- [ ] Test complete API request/response cycles
- [ ] Test database CRUD operations
- [ ] Test MinIO file upload/download

**Command**: `pytest tests/backend/integration/`

---

### Stage 3: Frontend Tests

#### Unit Tests
- [ ] Test Pinia store actions and mutations
- [ ] Test component rendering with mocked props

**Command**: `npm run test:unit`

#### E2E Tests (Playwright)
- [ ] Test user flow: Upload → Study Design visible
- [ ] Test user flow: Select Assay → Assemble Workflow
- [ ] Test user flow: Add nodes → Connect nodes
- [ ] Test user flow: Run Workflow → See status updates
- [ ] Test panel collapse/expand behavior

**Command**: `npx playwright test`

---

### Stage 4: Agent Tests

#### Unit Tests
- [ ] Test prompt formatting
- [ ] Test response parsing
- [ ] Test session context management

**Command**: `pytest tests/agents/unit/`

#### Integration Tests
- [ ] Test Scholar with sample PDF → ISA-JSON output
- [ ] Test Engineer with ISA-JSON → CWL output

**Command**: `pytest tests/agents/integration/`

---

### Stage 5: Execution Engine Tests

#### Unit Tests
- [ ] Test CWL parsing
- [ ] Test DAG generation logic

**Command**: `pytest tests/execution/unit/`

#### Integration Tests
- [ ] Test CWL→Airflow with sample workflow
- [ ] Test Docker container execution

**Command**: `pytest tests/execution/integration/`

---

### Stage 6: End-to-End Tests

#### E2E Tests (Playwright)
- [ ] Complete MAMA-MIA demo flow test
- [ ] Test error handling scenarios
- [ ] Test result visualization

**Command**: `npx playwright test tests/e2e/mama_mia_flow.spec.ts`

#### Manual Verification
- [ ] AI: Run complete demo flow, verify all steps succeed
- [ ] Developer: Sanity check visual design and interactions

---

## 6. Quality Gates

### Per-Stage Completion Criteria

| Stage | Criteria |
|-------|----------|
| Stage 1 | All Docker services healthy, databases initialized |
| Stage 2 | All API endpoints return valid responses, tests pass |
| Stage 3 | All UI modules render correctly, E2E tests pass |
| Stage 4 | Agents produce valid ISA-JSON and CWL from test inputs |
| Stage 5 | Sample workflow executes successfully in Airflow |
| Stage 6 | MAMA-MIA demo completes end-to-end, results visible |

### MVP Quality Requirements

- [ ] All unit tests passing (minimum 80% coverage for critical paths)
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] No critical or high-severity bugs
- [ ] Demo flow verified end-to-end by AI
- [ ] Console logs clear and informative
- [ ] Error messages user-friendly

---

## 7. Risks and Mitigations

### Stage 1 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Docker networking issues | High | Use host networking fallback, detailed troubleshooting guide |
| MinIO/Airflow version incompatibility | Medium | Pin specific versions in docker-compose |

### Stage 2 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex Pydantic models cause validation errors | Medium | Extensive unit tests, gradual model refinement |
| WebSocket implementation complexity | Medium | Start with polling, add WebSocket as enhancement |

### Stage 3 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| UI deviation from React source | High | Enforce strict UI porting contract and parity checklist |
| Panel resize/collapse state bugs | Medium | Comprehensive E2E tests for state persistence |

### Stage 4 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemini API rate limits during development | High | Cache responses, use mock data for tests |
| Poor extraction quality from PDF | High | Pre-process PDFs, provide context files |

### Stage 5 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| CWL→Airflow conversion edge cases | High | Start with simple workflows, add complexity gradually |
| Docker container build failures | Medium | Pre-built base images, cached layers |

### Stage 6 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Integration issues across components | High | Incremental integration, detailed logging |
| Performance issues with large workflows | Medium | Limit subject count, optimize queries |

---

## 8. Final Review and Handoff

### AI Verification Steps

Before requesting developer sign-off:

1. [ ] All automated tests pass (`pytest` and `playwright`)
2. [ ] MAMA-MIA demo flow executed successfully 3+ times
3. [ ] Error handling verified for common failure scenarios
4. [ ] Console logs reviewed for clarity
5. [ ] API responses match specification
6. [ ] UI matches visual design specifications
7. [ ] Documentation updated (README, API docs)

### Developer Sign-Off Checklist

- [ ] Docker Compose starts without errors
- [ ] All services accessible at expected ports
- [ ] MAMA-MIA demo flow works from start to finish
- [ ] Results appear correctly in right panel
- [ ] No console errors in browser DevTools
- [ ] Performance acceptable (no obvious lag)
- [ ] Code is reasonably clean and documented

### Handoff Artifacts

1. **PLAN.md** - This document (development plan)
2. **SPEC.md** - Technical specification (already exists)
3. **README.md** - Setup and usage instructions
4. **WALKTHROUGH.md** - Demo flow documentation
5. **API.md** - API endpoint documentation (already exists)

---

## Appendix A: Tech Stack Summary

| Component | Technology | Version |
|-----------|------------|---------|
| Frontend | Vue 3 + TypeScript | 3.x |
| Workflow Viz | Vue Flow | latest |
| State Mgmt | Pinia | latest |
| Styling | Tailwind CSS | 4.x |
| Backend | Python FastAPI | latest |
| Database | PostgreSQL | 15 |
| Object Storage | MinIO | latest |
| Workflow Engine | Apache Airflow | 2.8+ |
| AI Engine | Gemini 3 API (google-genai SDK) | gemini-3-pro-preview |
| Container Runtime | Docker | latest |

## Appendix B: File Structure

```
VeriFlow/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── publications.py
│   │   │   ├── workflows.py
│   │   │   ├── executions.py
│   │   │   └── catalogue.py
│   │   ├── agents/
│   │   │   ├── scholar.py
│   │   │   ├── engineer.py
│   │   │   └── reviewer.py
│   │   ├── models/
│   │   │   ├── isa.py
│   │   │   ├── workflow.py
│   │   │   └── session.py
│   │   ├── services/
│   │   │   ├── minio_client.py
│   │   │   ├── airflow_client.py
│   │   │   └── gemini_client.py
│   │   └── main.py
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadModule.vue
│   │   │   ├── StudyDesignModule.vue
│   │   │   ├── WorkflowCanvas.vue
│   │   │   ├── MeasurementNode.vue
│   │   │   ├── ToolNode.vue
│   │   │   ├── ModelNode.vue
│   │   │   ├── DataObjectCatalogue.vue
│   │   │   ├── ViewerPanel.vue
│   │   │   ├── DatasetNavigationModule.vue
│   │   │   └── ConsoleModule.vue
│   │   ├── stores/
│   │   │   └── workflow.ts
│   │   └── App.vue
│   ├── tests/
│   └── package.json
├── dags/
│   └── veriflow_template.py
├── docker-compose.yml
├── .env.example
├── SPEC.md
├── PLAN.md
└── README.md
```

---

**End of Plan**
