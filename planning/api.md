# VeriFlow MVP API Specification

**Status**: 🚀 MVP Specification
**Last Updated**: 2026-01-29
**Base URL**: `/api/v1`

---

## 1. Publication & Study Design

### Upload Publication
**POST** `/publications/upload`
Uploads a PDF to trigger the Scholar Agent for ingestion and ISA extraction.

**Request:** `multipart/form-data`
- `file`: PDF file

**Response:** `200 OK`
```json
{
  "upload_id": "pub_123",
  "filename": "study.pdf",
  "status": "processing",
  "message": "Scholar Agent analyzing..."
}
```

### Get Study Design (ISA Hierarchy)
**GET** `/study-design/{upload_id}`
Retrieves the extracted structure (Investigation -> Study -> Assays) for the left panel tree view.

**Response:** `200 OK`
```json
{
  "upload_id": "pub_123",
  "hierarchy": {
    "investigation": {
      "id": "inv_1",
      "title": "Automated Tumor Detection",
      "properties": [
        { "id": "inv-title", "value": "Automated Tumor Detection", "source_id": "citation_1" }
      ],
      "studies": [
        {
          "id": "study_1",
          "title": "MRI-based Segmentation",
          "assays": [
            {
              "id": "assay_1",
              "name": "U-Net Training",
              "steps": [
                { "id": "step_1", "description": "Data acquisition" }
              ]
            }
          ]
        }
      ]
    }
  }
}
```

### Update Node Property
**PUT** `/study-design/nodes/{node_id}/properties`
Updates editable properties (e.g., Title, Description) in the Review panel.

**Request:** `application/json`
```json
{
  "property_id": "inv-title",
  "value": "New Title"
}
```

---

## 2. Workflow Management

### Assemble Workflow from Assay
**POST** `/workflows/assemble`
Triggers the Engineer Agent to generate an initial workflow graph from a selected Assay.

**Request:** `application/json`
```json
{
  "assay_id": "assay_1"
}
```

**Response:** `200 OK`
```json
{
  "workflow_id": "wf_789",
  "graph": {
    "nodes": [
      { "id": "input-1", "type": "measurement", "data": { "label": "MRI Scans" }, "position": { "x": 50, "y": 50 } },
      { "id": "tool-1", "type": "tool", "data": { "label": "DICOM to NIfTI" }, "position": { "x": 450, "y": 50 } }
    ],
    "edges": [
      { "id": "e1-2", "source": "input-1", "target": "tool-1" }
    ]
  }
}
```

### Get Workflow
**GET** `/workflows/{workflow_id}`
Retrieves the current state of a workflow graph.

### Save Workflow
**PUT** `/workflows/{workflow_id}`
Saves the current node/edge configuration and positions.

**Request:** `application/json`
```json
{
  "graph": {
    "nodes": [...],
    "edges": [...]
  }
}
```

---

## 3. Data Object Catalogue

### List Catalogue Items
**GET** `/catalogue`
Lists all data objects, tools, and models. Supports filtering by "active" (used in current workflow).

**Query Params:**
- `workflow_id` (optional): If provided, marks items as `in_use: true` if they appear in the graph.
- `type`: `measurement | tool | model` (optional)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "tool-1",
      "type": "tool",
      "name": "DICOM to NIfTI",
      "category": "processing",
      "in_use": true
    }
  ]
}
```

### Update Catalogue Item
**PUT** `/catalogue/{item_id}`
Updates metadata for a tool or measurement (e.g., correcting a description).

---

## 4. Execution

### Run Workflow
**POST** `/executions`
Triggers the workflow execution via Airflow.

**Request:** `application/json`
```json
{
  "workflow_id": "wf_789",
  "config": {
    "subjects": [1, 384]
  }
}
```

**Response:** `202 Accepted`
```json
{
  "execution_id": "exec_456",
  "status": "queued"
}
```

### Get Execution Status
**GET** `/executions/{execution_id}`
Polls for overall progress and individual node status.

**Response:** `200 OK`
```json
{
  "execution_id": "exec_456",
  "status": "running",
  "overall_progress": 45,
  "nodes": {
    "tool-1": { "status": "completed", "progress": 100 },
    "tool-2": { "status": "running", "progress": 20 }
  },
  "logs": [
    { "timestamp": "...", "level": "INFO", "message": "Starting node tool-2..." }
  ]
}
```

### Get Results / Dataset Navigation
**GET** `/executions/{execution_id}/results`
Lists generated files for the 'Visualise & Export' panel.

**Query Params:**
- `node_id` (optional): Filter files by specific workflow node.

**Response:** `200 OK`
```json
{
  "files": [
    { "path": "derivative/subject_001/mask.nii.gz", "node_id": "tool-2", "size": 1024 }
  ]
}
```

---

## 5. Viewers & Sources

### Get Source Snippet
**GET** `/sources/{source_id}`
Retrieves the text snippet and PDF location metadata for a specific citation source.

**Response:** `200 OK`
```json
{
  "id": "citation_1",
  "text": "We collected 384 patients...",
  "pdf_location": { "page": 3, "rect": [...] }
}
```
