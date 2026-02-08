/**
 * VeriFlow Workflow Store
 * 
 * Central state management for the VeriFlow application.
 * Per SPEC.md Section 6.3
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Node, Edge } from '@vue-flow/core'
import { endpoints } from '../services/api'
import { veriflowApi } from '../services/veriflowApi'
import { useConsoleStore } from './console'
import { getLayoutedElements } from '../utils/layout'

// Types per SPEC.md Section 3
export interface ConfidenceScore {
    value: number
    source_page?: number
    source_text?: string
}

export interface ConfidenceScores {
    upload_id: string
    generated_at: string
    scores: Record<string, ConfidenceScore>
}

export interface Investigation {
    identifier: string
    title: string
    description: string
    studies: Study[]
}

export interface Study {
    identifier: string
    title: string
    description: string
    assays: Assay[]
}

export interface Assay {
    identifier?: string
    filename: string
    measurementType: { term: string }
    technologyType: { term: string }
}

export interface NodeStatus {
    status: 'pending' | 'running' | 'completed' | 'error'
    progress: number
}

export interface LogEntry {
    timestamp: string
    level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
    message: string
    node_id?: string
    agent?: string
}

export const useWorkflowStore = defineStore('workflow', () => {
    const consoleStore = useConsoleStore()

    // Upload state
    const uploadId = ref<string | null>(null)
    const uploadedPdfUrl = ref<string | null>(null)
    const hasUploadedFiles = ref(false)

    // Study design state
    const hierarchy = ref<Investigation | null>(null)
    const confidenceScores = ref<ConfidenceScores | null>(null)
    const selectedAssay = ref<string | null>(null)

    // Workflow state
    const workflowId = ref<string | null>(null)
    const nodes = ref<Node[]>([])
    const edges = ref<Edge[]>([])
    const isAssembled = ref(false)
    const selectedNode = ref<string | null>(null)
    const selectedDatasetId = ref<string | null>(null)

    // Execution state
    const executionId = ref<string | null>(null)
    const isWorkflowRunning = ref(false)
    const nodeStatuses = ref<Record<string, NodeStatus>>({})
    const nodeValidationStatus = ref<Record<string, any>>({})
    const logs = ref<LogEntry[]>([])
    const pollingInterval = ref<number | undefined>(undefined)

    // VeriFlow state
    const veriflowRunId = ref<string | null>(null)
    const veriflowSocket = ref<WebSocket | null>(null)

    // UI state
    const isLeftPanelCollapsed = ref(false)
    const isRightPanelCollapsed = ref(true)
    const isConsoleCollapsed = ref(true)
    const consoleHeight = ref(typeof window !== 'undefined' && window.innerHeight < 900 ? 220 : 300)
    const viewerPdfUrl = ref<string | null>(null)
    const isViewerVisible = ref(false)

    // Stage 6: Loading states and error handling
    const isLoading = ref(false)
    const loadingMessage = ref<string | null>(null)
    const error = ref<string | null>(null)

    // Computed
    const graph = computed(() => ({
        nodes: nodes.value,
        edges: edges.value,
    }))

    // Actions
    function uploadPublication(id: string, pdfUrl: string) {
        uploadId.value = id
        uploadedPdfUrl.value = pdfUrl
        hasUploadedFiles.value = true
        // Trigger study design fetch
        fetchStudyDesign(id)
    }

    // Stage 6: Load pre-loaded MAMA-MIA example
    async function loadExample(exampleName: string = 'mama-mia') {
        reset(); // Clear previous state
        isLoading.value = true
        loadingMessage.value = `Loading ${exampleName.toUpperCase()} demo...`
        error.value = null

        try {
            const response = await endpoints.loadExample(exampleName)
            const data = response.data

            uploadId.value = data.upload_id
            uploadedPdfUrl.value = null
            hasUploadedFiles.value = true

            // Directly process demo results from the response
            if (data.hierarchy) {
                processStudyDesignResult({"hierarchy": data.hierarchy});
            }

            if (data.engineer_output) {
                const graph = data.engineer_output.graph || { nodes: [], edges: [] };
                const validation_report = data.engineer_output.validation_report || {};
                nodeValidationStatus.value = validation_report;

                let finalEdges = graph.edges || [];
                if (Object.keys(validation_report).length > 0) {
                    const invalidNodeIds = new Set(
                        Object.entries(validation_report)
                            .filter(([_, result]) => (result as any).status === 'invalid')
                            .map(([key, _]) => key.replace('.cwl', ''))
                    );
                    finalEdges = (graph.edges || []).filter((edge: Edge) => 
                        !invalidNodeIds.has(edge.source) && !invalidNodeIds.has(edge.target)
                    );
                }
                const layouted = getLayoutedElements(graph.nodes || [], finalEdges, 'LR');
                nodes.value = layouted.nodes;
                edges.value = layouted.edges;
                isAssembled.value = true;
            }
            
            addLog({
                timestamp: new Date().toISOString(),
                level: 'INFO',
                message: `Loaded pre-configured ${exampleName.toUpperCase()} example with ground truth ISA hierarchy and mock workflow.`
            })

        } catch (err: any) {
            error.value = err.response?.data?.detail || err.message || 'Failed to load example'
            addLog({
                timestamp: new Date().toISOString(),
                level: 'ERROR',
                message: `Failed to load example: ${error.value}`
            })
        } finally {
            isLoading.value = false
            loadingMessage.value = null
        }
    }

    async function fetchStudyDesign(id: string) {
        // Try API first, fallback to mock
        try {
            await fetchStudyDesignFromApi(id)
        } catch (err) {
            console.log('API fetch failed, using mock data')
            // Mock hierarchy
            hierarchy.value = {
                identifier: 'inv_1',
                title: 'Automated Tumor Detection',
                description: 'Investigation description',
                studies: [{
                    identifier: 'study_1',
                    title: 'MRI-based Segmentation',
                    description: 'Study description',
                    assays: [{
                        identifier: 'assay_1',
                        filename: 'U-Net Training',
                        measurementType: { term: 'MRI' },
                        technologyType: { term: 'Imaging' }
                    }]
                }]
            } as any
        }
    }

    // Fetch study design from API
    async function fetchStudyDesignFromApi(id: string) {
        isLoading.value = true
        loadingMessage.value = 'Fetching study design...'

        try {
            const response = await endpoints.getStudyDesign(id)
            const data = response.data

            if (data.status === 'completed' && data.hierarchy) {
                // Set hierarchy from API response
                const inv = data.hierarchy.investigation
                hierarchy.value = {
                    identifier: inv.id || 'inv_1',
                    title: inv.title || 'Unknown Investigation',
                    description: inv.description || '',
                    studies: (inv.studies || []).map((study: any) => ({
                        identifier: study.id || 'study_1',
                        title: study.title || 'Unknown Study',
                        description: study.description || '',
                        assays: (study.assays || []).map((assay: any) => ({
                            identifier: assay.id,
                            filename: assay.name || 'Unknown Assay',
                            name: assay.name,
                            description: assay.description,
                            steps: assay.steps,
                            measurementType: { term: assay.measurement_type || 'Unknown' },
                            technologyType: { term: assay.technology_type || 'Unknown' }
                        }))
                    }))
                }

                // Set confidence scores
                if (data.confidence_scores) {
                    confidenceScores.value = data.confidence_scores as any
                }

                addLog({
                    timestamp: new Date().toISOString(),
                    level: 'INFO',
                    message: `Study design loaded: ${hierarchy.value.title}`
                })
            } else if (data.status === 'processing') {
                addLog({
                    timestamp: new Date().toISOString(),
                    level: 'INFO',
                    message: 'Study design is still being processed...'
                })
            } else if (data.status === 'error') {
                throw new Error('Study design extraction failed')
            }
        } finally {
            isLoading.value = false
            loadingMessage.value = null
        }
    }

    function setHierarchy(data: Investigation) {
        hierarchy.value = data
    }

    function selectAssay(assayId: string) {
        selectedAssay.value = assayId
    }

    async function assembleWorkflow(assayId: string) {
        console.log('Assembling workflow for assay:', assayId)

        isLoading.value = true
        loadingMessage.value = 'Assembling workflow with AI Agents...'
        error.value = null

        try {
            const response = await endpoints.assembleWorkflow(assayId)
            const data = response.data

            // Update store with graph data from backend
            workflowId.value = data.workflow_id

            // Map backend VueFlow nodes/edges to store
            if (data.graph) {
                const rawNodes = data.graph.nodes || []
                const rawEdges = data.graph.edges || []

                // Apply Auto-Layout
                const layouted = getLayoutedElements(rawNodes, rawEdges, 'LR')

                nodes.value = layouted.nodes
                edges.value = layouted.edges
            }

            isAssembled.value = true

            addLog({
                timestamp: new Date().toISOString(),
                level: 'INFO',
                message: `Workflow assembled successfully: ${data.workflow_id}`
            })

        } catch (err: any) {
            console.error('Workflow assembly failed:', err)
            error.value = err.response?.data?.detail || err.message || 'Failed to assemble workflow'

            addLog({
                timestamp: new Date().toISOString(),
                level: 'ERROR',
                message: `Workflow assembly failed: ${error.value}`
            })

            // Re-throw if needed, or handle gracefully
            // For now, we let the UI handle the error state via the error ref
        } finally {
            isLoading.value = false
            loadingMessage.value = null
        }
    }

    function setWorkflow(wfId: string, graphNodes: Node[], graphEdges: Edge[]) {
        workflowId.value = wfId
        nodes.value = graphNodes
        edges.value = graphEdges
        isAssembled.value = true
    }

    function updateNodeStatus(nodeId: string, status: NodeStatus) {
        nodeStatuses.value[nodeId] = status
    }

    // Helper to process study design results from various sources (API, WebSocket, Demo)
    function processStudyDesignResult(data: { hierarchy: any, confidence_scores: any, upload_id?: string }) {
        if (data.hierarchy) {
            const inv = data.hierarchy.investigation
            hierarchy.value = {
                identifier: inv.id || 'inv_1',
                title: inv.title || 'Unknown Investigation',
                description: inv.description || '',
                studies: (inv.studies || []).map((study: any) => ({
                    identifier: study.id || 'study_1',
                    title: study.title || 'Unknown Study',
                    description: study.description || '',
                    assays: (study.assays || []).map((assay: any) => ({
                        identifier: assay.id,
                        filename: assay.name || 'Unknown Assay',
                        name: assay.name,
                        description: assay.description,
                        steps: assay.steps,
                        measurementType: { term: assay.measurement_type || 'Unknown' },
                        technologyType: { term: assay.technology_type || 'Unknown' }
                    }))
                }))
            }
        }

        if (data.confidence_scores) {
            confidenceScores.value = {
                upload_id: data.upload_id || uploadId.value || 'unknown',
                generated_at: new Date().toISOString(),
                scores: data.confidence_scores
            }
        }

        addLog({
            timestamp: new Date().toISOString(),
            level: 'INFO',
            message: `Study design loaded: ${hierarchy.value?.title || 'Unknown'}`
        })
        hasUploadedFiles.value = true // Indicate that study design data is available
    }

    function addLog(entry: LogEntry) {
        logs.value.push(entry)
        consoleStore.addMessage({
            type: 'system',
            content: entry.message
        })
    }

    async function runVeriflowWorkflow(pdfFile: File, contextFile?: File) {
        console.log("runVeriflowWorkflow called with:", { pdfFile, contextFile });
        reset(); // Clear previous state
        try {
            isLoading.value = true
            loadingMessage.value = "Analyzing document..."
            const response = await veriflowApi.runVeriflow(pdfFile, contextFile)
            veriflowRunId.value = response.data.run_id
            isWorkflowRunning.value = true
            connectToVeriflowSocket(response.data.run_id)
        } catch (err: any) {
            error.value = err.response?.data?.detail || err.message || 'Failed to start VeriFlow workflow'
            addLog({
                timestamp: new Date().toISOString(),
                level: 'ERROR',
                message: `Failed to start VeriFlow workflow: ${error.value}`
            })
            isLoading.value = false
            loadingMessage.value = null
        }
    }

    function connectToVeriflowSocket(runId: string) {
        console.log("connectToVeriflowSocket called with runId:", runId);
        if (veriflowSocket.value) {
            veriflowSocket.value.close()
        }

        veriflowSocket.value = veriflowApi.connectToWebSocket(runId, async (event) => {
            console.log("WebSocket message received:", event)
            
            // Log progress
            if (event.type === 'node_update' || event.type.endsWith('_complete')) {
                addLog({
                    timestamp: new Date().toISOString(),
                    level: 'INFO',
                    message: `Status: ${event.type}`
                })
            }

            // When workflow is complete, fetch the final results via REST
            if (event.type === 'workflow_complete') {
                isWorkflowRunning.value = false
                isLoading.value = false
                loadingMessage.value = null
                veriflowSocket.value?.close()
                
                // Fetch the full results
                await fetchAndProcessResults(runId);

            } else if (event.type === 'error') {
                addLog({
                    timestamp: new Date().toISOString(),
                    level: 'ERROR',
                    message: `Workflow error: ${event.data}`,
                    agent: 'system'
                })
                isWorkflowRunning.value = false
                isLoading.value = false
                loadingMessage.value = null
                veriflowSocket.value?.close()
            }
        })
    }

    async function fetchAndProcessResults(runId: string) {
        console.log("fetchAndProcessResults called for runId:", runId);
        try {
            isLoading.value = true;
            loadingMessage.value = "Fetching final results...";
            
            const response = await endpoints.getVeriflowResults(runId);
            const results = response.data;
            console.log("fetchAndProcessResults received raw results:", results);

            // Process Scholar results
            if (results.scholar) {
                const scholarData = {
                    hierarchy: { investigation: results.scholar.isa_json || {} },
                    confidence_scores: results.scholar.confidence_scores || {}
                };
                console.log("fetchAndProcessResults processed scholarData:", scholarData);
                processStudyDesignResult(scholarData);
            }

            // Process Engineer results
            if (results.engineer) {
                const engineerData = results.engineer || {};
                console.log("fetchAndProcessResults processed engineerData:", engineerData);
                const graph = engineerData.graph || { nodes: [], edges: [] };
                const validation_report = engineerData.validation_report || {};
                
                nodeValidationStatus.value = validation_report;
                let finalEdges = graph.edges || [];

                if (Object.keys(validation_report).length > 0) {
                    const invalidNodeIds = new Set(
                        Object.entries(validation_report)
                            .filter(([_, result]) => (result as any).status === 'invalid')
                            .map(([key, _]) => key.replace('.cwl', ''))
                    );
                    
                    finalEdges = (graph.edges || []).filter((edge: Edge) => 
                        !invalidNodeIds.has(edge.source) && !invalidNodeIds.has(edge.target)
                    );
                }
                const layouted = getLayoutedElements(graph.nodes || [], finalEdges, 'LR');
                nodes.value = layouted.nodes;
                edges.value = layouted.edges;
                isAssembled.value = true;
            }

        } catch (err: any) {
            error.value = err.response?.data?.detail || err.message || 'Failed to fetch results';
            addLog({
                timestamp: new Date().toISOString(),
                level: 'ERROR',
                message: `Result fetch failed: ${error.value}`
            });
        } finally {
            isLoading.value = false;
            loadingMessage.value = null;
        }
    }

    function toggleLeftPanel() {
        isLeftPanelCollapsed.value = !isLeftPanelCollapsed.value
    }

    function toggleRightPanel() {
        isRightPanelCollapsed.value = !isRightPanelCollapsed.value
    }

    function toggleConsole() {
        isConsoleCollapsed.value = !isConsoleCollapsed.value
    }

    // Stage 6: Export execution results as SDS ZIP
    async function exportResults() {
        if (!executionId.value) {
            error.value = 'No execution to export'
            return
        }

        isLoading.value = true
        loadingMessage.value = 'Generating export...'

        try {
            const response = await endpoints.exportExecution(executionId.value)

            // Create download link
            const blob = new Blob([response.data as any], { type: 'application/zip' })
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = `veriflow_export_${executionId.value}.zip`
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)

            addLog({
                timestamp: new Date().toISOString(),
                level: 'INFO',
                message: `Exported results to veriflow_export_${executionId.value}.zip`
            })
        } catch (err: any) {
            error.value = err.response?.data?.detail || err.message || 'Failed to export'
            addLog({
                timestamp: new Date().toISOString(),
                level: 'ERROR',
                message: `Export failed: ${error.value}`
            })
        } finally {
            isLoading.value = false
            loadingMessage.value = null
        }
    }

    // Clear error
    function clearError() {
        error.value = null
    }

    function reset() {
        uploadId.value = null
        uploadedPdfUrl.value = null
        hasUploadedFiles.value = false
        hierarchy.value = null
        confidenceScores.value = null
        selectedAssay.value = null
        workflowId.value = null
        nodes.value = []
        edges.value = []
        isAssembled.value = false
        selectedNode.value = null
        selectedDatasetId.value = null
        executionId.value = null
        isWorkflowRunning.value = false
        nodeStatuses.value = {}
        nodeValidationStatus.value = {}
        logs.value = []
        if (pollingInterval.value) clearInterval(pollingInterval.value)
    }

    return {
        // State
        uploadId,
        uploadedPdfUrl,
        hasUploadedFiles,
        hierarchy,
        confidenceScores,
        selectedAssay,
        workflowId,
        nodes,
        edges,
        isAssembled,
        selectedNode,
        selectedDatasetId,
        executionId,
        isWorkflowRunning,
        nodeStatuses,
        nodeValidationStatus,
        logs,
        isLeftPanelCollapsed,
        isRightPanelCollapsed,
        isConsoleCollapsed,
        consoleHeight,
        viewerPdfUrl,
        isViewerVisible,
        isLoading,
        loadingMessage,
        error,
        veriflowRunId,
        veriflowSocket,

        // Computed
        graph,

        // Actions
        uploadPublication,
        fetchStudyDesign,
        setHierarchy,
        selectAssay,
        assembleWorkflow,
        setWorkflow,
        updateNodeStatus,
        addLog,
        runVeriflowWorkflow,
        toggleLeftPanel,
        toggleRightPanel,
        toggleConsole,
        reset,
        loadExample,
        fetchStudyDesignFromApi,
        exportResults,
        clearError,
    }
})
