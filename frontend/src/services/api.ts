import axios from 'axios'

const api = axios.create({
    // Use relative path to leverage Vite proxy (dev) and Nginx proxy (prod)
    baseURL: '/api/v1',
    timeout: 0, // No timeout for long-running orchestration processes
    headers: {
        'Content-Type': 'application/json'
    }
})

// Types
export interface UploadResponse {
    upload_id: string
    filename: string
    status: string
    message: string
    pdf_path?: string
    folder_path?: string
}

export interface HierarchyResponse {
    upload_id: string
    status: string
    hierarchy: any
    confidence_scores?: any
}

export interface WorkflowResponse {
    workflow_id: string
    graph: any
}

export interface ExecutionResponse {
    execution_id: string
    status: string
}

export interface ExecutionStatusResponse {
    execution_id: string
    status: string
    overall_progress: number
    nodes: Record<string, { status: string; progress: number }>
    logs: any[]
}

export const endpoints = {
    // Publication & Study Design
    uploadPublication: (file: File) => {
        const formData = new FormData()
        formData.append('file', file)
        return api.post<UploadResponse>('/publications/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    uploadPublicationWithId: (file: File, pdfId: string) => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('pdf_id', pdfId)
        return api.post<UploadResponse>('/publications/upload_with_id', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    // Stage 6: Load pre-loaded example (MAMA-MIA demo)
    loadExample: (exampleName: string = 'mama-mia') =>
        api.post<UploadResponse>('/publications/load-example', { example_name: exampleName }),

    getStudyDesign: (uploadId: string) =>
        api.get<HierarchyResponse>(`/study-design/${uploadId}`),

    updateNodeProperty: (nodeId: string, propertyId: string, value: string) =>
        api.put(`/study-design/nodes/${nodeId}/properties`, { property_id: propertyId, value }),

    sendAdditionalInfo: (uploadId: string, info: string) =>
        api.post(`/publications/${uploadId}/additional-info`, { info }),

    // Workflow Management
    assembleWorkflow: (assayId: string) =>
        api.post<WorkflowResponse>('/workflows/assemble', { assay_id: assayId }),

    getWorkflow: (workflowId: string) =>
        api.get<WorkflowResponse>(`/workflows/${workflowId}`),

    saveWorkflow: (workflowId: string, graph: any) =>
        api.put(`/workflows/${workflowId}`, { graph }),

    // Catalogue
    getCatalogue: (workflowId?: string) =>
        api.get('/catalogue', { params: { workflow_id: workflowId } }),

    // Execution
    runWorkflow: (workflowId: string, config: any) =>
        api.post<ExecutionResponse>('/executions', { workflow_id: workflowId, config }),

    getExecutionStatus: (executionId: string) =>
        api.get<ExecutionStatusResponse>(`/executions/${executionId}`),

    getResults: (executionId: string, nodeId?: string) =>
        api.get(`/executions/${executionId}/results`, { params: { node_id: nodeId } }),

    // Stage 6: Export execution as SDS ZIP
    exportExecution: (executionId: string) =>
        api.get(`/executions/${executionId}/export`, { responseType: 'blob' }),

    // Viewers
    getSourceSnippet: (sourceId: string) =>
        api.get(`/sources/${sourceId}`),

    // Orchestrate Workflow
    orchestrateWorkflow: (pdfPath: string, repoPath: string, clientId?: string) =>
        api.post<OrchestrationResponse>('/orchestrate', { pdf_path: pdfPath, repo_path: repoPath, client_id: clientId }),

    // Cached MAMA-MIA Demo
    mamaMiaCache: (clientId?: string) =>
        api.get<OrchestrationResponse>('/mama-mia-cache', { params: { client_id: clientId } }),

    // Artifact Retrieval (Polling)
    getArtifact: (runId: string, agentName: string) =>
        api.get(`/orchestrate/${runId}/artifacts/${agentName}`)
}

export interface OrchestrationResponse {
    status: string
    message: string
    result: {
        isa_json: any
        generated_code: any
        review_decision: string
        review_feedback: string
        errors: string[]
    }
}

export default api
