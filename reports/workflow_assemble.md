# Workflow Assembly Implementation Analysis

**Date:** 2026-02-04
**Topic:** Backend Implementation & Frontend Integration Status

## 1. Executive Summary
The backend infrastructure for workflow assembly is **fully implemented and ready**, including endpoints, data models, and logic (both AI-based and fallback). However, the frontend is currently running on **mock data** and has not yet been connected to these live endpoints.

## 2. Backend Implementation Status
**Location:** `backend/app/api/workflows.py`

### Endpoints
- **`POST /workflows/assemble`**: Accepts an `assay_id` and returns a complete graph (Nodes + Edges) ready for Vue Flow.
- **`GET /workflows/{id}`**: Retrieves stored workflow state.
- **`PUT /workflows/{id}`**: Saves workflow state.

### Logic
1.  **AI-Driven Generation**: Checks for `AGENTS_AVAILABLE`. If true, invokes the **Engineer Agent** to generate CWL and a Vue Flow graph based on ISA-JSON metadata (cached from upload).
2.  **Fallback Mechanism**: If agents are unavailable or fail, it falls back to a hardcoded "MAMA-MIA" example workflow, ensuring the UI always has data to display for demo purposes.

### Data Models
**Location:** `backend/app/models/workflow.py`
The backend uses Pydantic models to strictly enforce the JSON structure required by the frontend's Vue Flow library.

-   **`VueFlowNode`**:
    ```json
    {
      "id": "string",
      "type": "tool | measurement | model",
      "position": { "x": 0, "y": 0 },
      "data": {
        "label": "string",
        "inputs": [],
        "outputs": [],
        "status": "pending"
      }
    }
    ```
-   **`VueFlowEdge`**:
    ```json
    {
      "id": "string",
      "source": "node-id",
      "target": "node-id",
      "sourceHandle": "port-id",
      "targetHandle": "port-id"
    }
    ```

## 3. Frontend Implementation Status
**Location:** `frontend/src/stores/workflow.ts`

-   **API Client**: `api.ts` correctly defines the client methods (`endpoints.assembleWorkflow`).
-   **Current State**: The `workflow` store is currently **USING MOCK DATA**.
    -   `assembleWorkflow(assayId)` function constructs a hardcoded JavaScript object array for `nodes` and `edges`.
    -   It does **not** call the API endpoint.

## 4. Next Steps (Integration Plan)
To enable real functionality, the following changes are required in `frontend/src/stores/workflow.ts`:

1.  **Switch to Async API Call**:
    ```typescript
    // Replace mock logic with:
    const response = await endpoints.assembleWorkflow(assayId)
    this.nodes = response.data.graph.nodes
    this.edges = response.data.graph.edges
    this.workflowId = response.data.workflow_id
    ```
2.  **Error Handling**: Wrap the call in `try/catch` to handle network or execution errors.
