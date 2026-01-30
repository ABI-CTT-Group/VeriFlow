import axios from 'axios'

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1', // Adjust per your backend setup
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

    // Stage 6: Load pre-loaded example (MAMA-MIA demo)
    loadExample: (exampleName: string = 'mama-mia') =>
        api.post<UploadResponse>('/publications/load-example', { example_name: exampleName }),

    getStudyDesign: (uploadId: string) =>
        api.get<HierarchyResponse>(`/study-design/${uploadId}`),

    updateNodeProperty: (nodeId: string, propertyId: string, value: string) =>
        api.put(`/study-design/nodes/${nodeId}/properties`, { property_id: propertyId, value }),

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
        api.get(`/sources/${sourceId}`)
}

export default api
