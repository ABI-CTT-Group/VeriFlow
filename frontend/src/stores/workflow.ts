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
    const logs = ref<LogEntry[]>([])
    const pollingInterval = ref<number | undefined>(undefined)

    // UI state
    const isLeftPanelCollapsed = ref(false)
    const isRightPanelCollapsed = ref(true)
    const isConsoleCollapsed = ref(true)
    const consoleHeight = ref(200)
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
        isLoading.value = true
        loadingMessage.value = `Loading ${exampleName.toUpperCase()} demo...`
        error.value = null

        try {
            const response = await endpoints.loadExample(exampleName)
            const data = response.data

            uploadId.value = data.upload_id
            uploadedPdfUrl.value = null // No actual PDF for pre-loaded examples
            hasUploadedFiles.value = true

            addLog({
                timestamp: new Date().toISOString(),
                level: 'INFO',
                message: `Loaded pre-configured ${exampleName.toUpperCase()} example`
            })

            // Fetch study design for the loaded example
            await fetchStudyDesignFromApi(data.upload_id)

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
        // Mock assembly
        workflowId.value = `wf_${Date.now()}`
        isAssembled.value = true

        // Populate with mock nodes (Vue Flow structure)
        nodes.value = [
            {
                id: 'input-1',
                type: 'measurement',
                position: { x: 50, y: 50 },
                data: {
                    role: 'input',
                    name: 'Input Measurements',
                    outputs: [
                        { id: 'out-0', label: 'MRI Scan', datasetId: 'dce-mri-scans', sampleId: 'Subject_001/T1w.nii.gz' }
                    ],
                    totalSubjects: 384
                }
            },
            {
                id: 'tool-1',
                type: 'tool',
                position: { x: 450, y: 50 },
                data: {
                    name: 'DICOM to NIfTI',
                    status: 'completed',
                    confidence: 0.95,
                    inputs: [{ id: 'in-0', label: 'Raw DICOM' }],
                    outputs: [{ id: 'out-0', label: 'NIfTI Volume' }]
                }
            },
            {
                id: 'tool-2',
                type: 'tool',
                position: { x: 800, y: 50 },
                data: {
                    name: 'nnU-Net Segmentation',
                    status: 'running',
                    confidence: 0.88,
                    inputs: [
                        { id: 'in-0', label: 'NIfTI Volume' },
                        { id: 'in-1', label: 'Model Weights' }
                    ],
                    outputs: [{ id: 'out-0', label: 'Segmentation Mask' }]
                }
            },
            {
                id: 'model-1',
                type: 'model',
                position: { x: 450, y: 320 },
                data: {
                    name: 'nnU-Net Pretrained Weights',
                    outputs: [{ id: 'out-0', label: 'Weights' }]
                }
            },
            {
                id: 'tool-3',
                type: 'tool',
                position: { x: 1150, y: 50 },
                data: {
                    name: 'Post-processing',
                    status: 'pending',
                    confidence: 0.92,
                    inputs: [{ id: 'in-0', label: 'Segmentation Mask' }],
                    outputs: [{ id: 'out-0', label: 'Refined Mask' }]
                }
            },
            {
                id: 'output-1',
                type: 'measurement',
                position: { x: 1500, y: 50 },
                data: {
                    name: 'Output Measurements',
                    role: 'output',
                    inputs: [
                        { id: 'in-0', label: 'Result', datasetId: 'tumor-segmentation', sampleId: 'Subject_001/tumor_mask.nii.gz' }
                    ]
                }
            }
        ] as Node[]

        edges.value = [
            { id: 'conn-1', source: 'input-1', sourceHandle: 'out-0', target: 'tool-1', targetHandle: 'in-0' },
            { id: 'conn-2', source: 'tool-1', sourceHandle: 'out-0', target: 'tool-2', targetHandle: 'in-0' },
            { id: 'conn-3', source: 'model-1', sourceHandle: 'out-0', target: 'tool-2', targetHandle: 'in-1' },
            { id: 'conn-4', source: 'tool-2', sourceHandle: 'out-0', target: 'tool-3', targetHandle: 'in-0' },
            { id: 'conn-5', source: 'tool-3', sourceHandle: 'out-0', target: 'output-1', targetHandle: 'in-0' }
        ] as Edge[]
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

    function addLog(entry: LogEntry) {
        logs.value.push(entry)
    }

    async function runWorkflow() {
        if (!workflowId.value) return

        try {
            isWorkflowRunning.value = true
            addLog({ timestamp: new Date().toISOString(), level: 'INFO', message: 'Starting workflow execution...' })

            // Mock execution start
            executionId.value = `exec_${Date.now()}`

            startPolling()
        } catch (error) {
            console.error('Execution failed:', error)
            isWorkflowRunning.value = false
            addLog({ timestamp: new Date().toISOString(), level: 'ERROR', message: 'Execution failed to start' })
        }
    }

    function startPolling() {
        if (pollingInterval.value) clearInterval(pollingInterval.value)

        pollingInterval.value = window.setInterval(async () => {
            if (!executionId.value) return
            simulateProgress()
        }, 2000)
    }

    function simulateProgress() {
        // Mock progress
        const nodeIds = nodes.value.map(n => n.id)
        const randomNode = nodeIds[Math.floor(Math.random() * nodeIds.length)]

        if (randomNode) {
            updateNodeStatus(randomNode, {
                status: 'running',
                progress: Math.floor(Math.random() * 100)
            })
            addLog({
                timestamp: new Date().toISOString(),
                level: 'INFO',
                message: `Node ${randomNode} progress update`,
                node_id: randomNode
            })
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
        runWorkflow,
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
