# VeriFlow MVP Development Plan

**Version**: 1.0.0  
**Created**: 2026-01-29  
**Target**: Hackathon MVP  

---

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

## 2. Development Stages

### Stage 1: Infrastructure & Foundation
**Entry Criteria**: Project repository initialized  
**Exit Criteria**: Docker Compose running, all services accessible, database schema applied

### Stage 2: Backend Core APIs
**Entry Criteria**: Stage 1 complete  
**Exit Criteria**: All API endpoints functional with mock data, Pydantic models validated

### Stage 3: Frontend Vue.js Application
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

## 3. Tasks per Stage

### Stage 1: Infrastructure & Foundation

#### AI Tasks
- [ ] Create `docker-compose.yml` with all services (FastAPI, PostgreSQL, MinIO, Airflow)
- [ ] Create PostgreSQL database schema (`agent_sessions`, `conversation_history`, `executions`)
- [ ] Configure MinIO buckets (`measurements`, `workflow`, `workflow-tool`, `process`)
- [ ] Create Airflow DAGs folder structure
- [ ] Write environment variable configuration (`.env.example`)
- [ ] Create FastAPI project skeleton with routers
- [ ] Create Vue 3 project with Vite and Vue Flow

#### Developer Tasks
- [ ] Obtain Gemini API key and set `GEMINI_API_KEY` environment variable
- [ ] Run `docker-compose up` to verify all services start
- [ ] Validate MinIO console accessible at `localhost:9001`
- [ ] Validate Airflow web UI accessible at `localhost:8080`

---

### Stage 2: Backend Core APIs

#### AI Tasks
- [ ] Implement Pydantic models for all data structures:
  - [ ] `SDSManifestRow`
  - [ ] `Investigation`, `Study`, `Assay` (ISA-JSON)
  - [ ] `ConfidenceScores`
  - [ ] `WorkflowGraph`, `VueFlowNode`, `VueFlowEdge`
  - [ ] `AgentSession`, `Message`
- [ ] Implement Publication API:
  - [ ] `POST /publications/upload` - File upload with MinIO storage
  - [ ] `GET /study-design/{upload_id}` - Return ISA hierarchy
  - [ ] `PUT /study-design/nodes/{node_id}/properties` - Update property
- [ ] Implement Workflow API:
  - [ ] `POST /workflows/assemble` - Generate graph from assay
  - [ ] `GET /workflows/{workflow_id}` - Get workflow state
  - [ ] `PUT /workflows/{workflow_id}` - Save workflow
- [ ] Implement Catalogue API:
  - [ ] `GET /catalogue` - List all data objects
  - [ ] `PUT /catalogue/{item_id}` - Update item metadata
- [ ] Implement Execution API:
  - [ ] `POST /executions` - Trigger workflow run
  - [ ] `GET /executions/{execution_id}` - Get execution status
  - [ ] `GET /executions/{execution_id}/results` - Get result files
- [ ] Implement WebSocket endpoint:
  - [ ] `ws://localhost:8000/ws/logs` - Real-time log streaming
- [ ] Implement Viewer API:
  - [ ] `GET /sources/{source_id}` - Get PDF citation snippet
- [ ] Create MinIO service layer for presigned URLs
- [ ] Create PostgreSQL service layer for session management

#### Developer Tasks
- [ ] Verify API endpoints with Postman/curl
- [ ] Confirm database tables created correctly

---

### Stage 3: Frontend Vue.js Application

#### AI Tasks
- [ ] Set up Vue 3 + TypeScript + Vite project
- [ ] Install dependencies: Vue Flow, Pinia, Tailwind CSS 4, Lucide icons
- [ ] Create Pinia store for workflow state:
  - [ ] `uploadId`, `uploadedPdfUrl`, `hasUploadedFiles`
  - [ ] `hierarchy`, `confidenceScores`, `selectedAssay`
  - [ ] `workflowId`, `graph`, `isAssembled`, `selectedNode`
  - [ ] `executionId`, `isWorkflowRunning`, `nodeStatuses`, `logs`
  - [ ] UI state: panel collapse states, console height
- [ ] Implement Left Panel:
  - [ ] `UploadModule.vue` - Drag-and-drop file upload
  - [ ] `StudyDesignModule.vue` - Tree view with confidence scores
- [ ] Implement Center Panel:
  - [ ] `WorkflowCanvas.vue` - Vue Flow integration with custom nodes
  - [ ] `MeasurementNode.vue` - Blue node with dataset selectors
  - [ ] `ToolNode.vue` - Purple node with input/output ports
  - [ ] `ModelNode.vue` - Green node with config params
  - [ ] `DataObjectCatalogue.vue` - Tree view of data objects
  - [ ] `ViewerPanel.vue` - PDF viewer with plugin system
- [ ] Implement Right Panel:
  - [ ] `DatasetNavigationModule.vue` - File tree viewer
- [ ] Implement Bottom Panel:
  - [ ] `ConsoleModule.vue` - Real-time logs with resize
- [ ] Implement panel resize and collapse functionality
- [ ] Implement drag-and-drop between catalogue and canvas
- [ ] Implement node connection logic (output→input ports)
- [ ] Implement "Run Workflow" button with status updates
- [ ] Connect all components to backend APIs

#### Developer Tasks
- [ ] Review component visual design matches specifications
- [ ] Verify drag-and-drop interactions work correctly

---

### Stage 4: Agent Integration (Gemini)

#### AI Tasks
- [ ] Create Gemini API client wrapper
- [ ] Implement Scholar Agent:
  - [ ] System prompt for PDF parsing and ISA extraction
  - [ ] PDF text extraction using PyMuPDF
  - [ ] ISA-JSON output generation
  - [ ] Confidence score generation
- [ ] Implement Engineer Agent:
  - [ ] System prompt for CWL generation
  - [ ] Dependency inference from code
  - [ ] Dockerfile generation
  - [ ] Adapter generation for type mismatches
- [ ] Implement Reviewer Agent:
  - [ ] System prompt for validation
  - [ ] CWL syntax validation
  - [ ] Error translation to user-friendly messages
- [ ] Implement session context management
- [ ] Store conversation history in PostgreSQL
- [ ] Create pre-loaded example configuration:
  - [ ] MAMA-MIA PDF and context file
  - [ ] Ground truth ISA-JSON for validation

#### Developer Tasks
- [ ] Verify Gemini API responses match expected formats
- [ ] Test agent prompts produce reasonable outputs

---

### Stage 5: Workflow Execution Engine

#### AI Tasks
- [ ] Implement CWL→Airflow DAG conversion:
  - [ ] Parse CWL v1.3 workflow YAML
  - [ ] Map `CommandLineTool` to `DockerOperator`
  - [ ] Handle step dependencies
  - [ ] Configure MinIO mounts
- [ ] Implement Airflow API client:
  - [ ] JWT authentication
  - [ ] DAG trigger
  - [ ] Status polling (5-second interval)
  - [ ] Log retrieval
- [ ] Implement Docker image building:
  - [ ] Generate Dockerfiles from tool CWL
  - [ ] Build and push to local registry
- [ ] Implement execution status WebSocket streaming
- [ ] Implement results storage in MinIO `process` bucket
- [ ] Implement provenance linking (wasDerivedFrom)

#### Developer Tasks
- [ ] Verify DAGs appear in Airflow UI
- [ ] Manually trigger sample DAG to verify Docker execution

---

### Stage 6: End-to-End Integration

#### AI Tasks
- [ ] Integrate all components for MAMA-MIA demo flow:
  - [ ] Load pre-loaded PDF example
  - [ ] Scholar extracts ISA hierarchy
  - [ ] User selects assay
  - [ ] Engineer generates workflow graph
  - [ ] User runs workflow
  - [ ] Results displayed in right panel
- [ ] Implement error handling for all failure modes
- [ ] Add console logging for all operations
- [ ] Implement SDS export functionality (ZIP download)
- [ ] Performance optimization and loading states

#### Developer Tasks
- [ ] Complete walkthrough of demo flow
- [ ] Verify results match expected outputs
- [ ] Sign off on MVP completion

---

## 4. Testing Plan per Stage

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

## 5. Quality Gates

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

## 6. Risks and Mitigations

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
| Vue Flow learning curve | Medium | Use existing UI code from `planning/UI/src` as reference |
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

## 7. Final Review and Handoff

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
| AI Engine | Gemini API | gemini-3-pro |
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
