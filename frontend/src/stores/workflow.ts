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
import { getLayoutedElements } from '../utils/layout'
import { wsService } from '../services/websocket'
import { useConsoleStore } from './console'

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
    steps?: any[]
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

    // Stage 6: Real-time Updates via WebSocket
    const clientId = ref<string | null>(null)

    async function initWebSocket() {
        if (!clientId.value) {
            clientId.value = typeof crypto !== 'undefined' && crypto.randomUUID
                ? crypto.randomUUID()
                : `client_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
        }

        if (wsService.isConnected && wsService.getClientId() === clientId.value) {
            return
        }

        await wsService.connect(clientId.value)

        // Setup Listeners
        const consoleStore = useConsoleStore()

        // Agent Thoughts/Stream
        wsService.on('agent_stream', (data) => {
            consoleStore.appendAgentMessage(data.agent.toLowerCase(), data.chunk)
        })

        // Status Updates
        wsService.on('status_update', (data) => {
            // Check if message starts with "Agent Name:"
            const agentMatch = data.message.match(/^([a-zA-Z]+) Agent:/)

            if (agentMatch) {
                const agentName = agentMatch[1].toLowerCase()
                consoleStore.addMessage({
                    type: 'agent',
                    agent: agentName as any,
                    content: data.message.replace(`${agentMatch[0]} `, ''),
                    timestamp: new Date()
                })
            } else {
                consoleStore.addSystemMessage(data.message)
            }

            // Only update loading message if we are actually loading something
            if (isLoading.value) {
                loadingMessage.value = data.message
            }
        })
    }
    async function loadExample(exampleName: string = 'mama-mia') {
        isLoading.value = true
        loadingMessage.value = `Orchestrating ${exampleName.toUpperCase()} demo...`
        error.value = null

        try {
            // Stage 6: Real-time Updates via WebSocket
            // Ensure we are connected
            if (!wsService.isConnected && clientId.value) {
                await initWebSocket()
            } else if (!clientId.value) {
                await initWebSocket()
            }

            // Use existing clientId
            const currentClientId = clientId.value!
            let response;

            if (exampleName === 'mama-mia') {
                response = await endpoints.mamaMiaCache(currentClientId)
            } else {
                // Use Orchestration API
                const pdfPath = "/app/examples/mama-mia/1.pdf"
                const repoPath = "/app/examples/mama-mia"

                // Pass clientId to backend
                response = await endpoints.orchestrateWorkflow(pdfPath, repoPath, currentClientId)
            }

            const data = response.data
            console.log("Orchestration Response: ", data);

            console.log("data.status: ", data.status);
            console.log("data.result: ", data.result);
            console.log(data.status === 'completed' && data.result)


            if (data.status === 'completed' && data.result) {
                // Generate a pseudo upload ID
                uploadId.value = `orch_${Date.now()}`
                uploadedPdfUrl.value = null
                hasUploadedFiles.value = true

                // Map ISA JSON to Hierarchy
                // The orchestration result structure: { studyDesign: { ... } }
                // We need to map this to our Investigation interface
                const isa = data.result.isa_json
                console.log("ISA: ", isa);
                if (isa && isa.studyDesign) {
                    const sd = isa.studyDesign
                    const inv = sd.investigation || {}
                    console.log("Investigation: ", inv);
                    // Construct Hierarchy
                    hierarchy.value = {
                        identifier: inv.id || 'inv_orchestrated',
                        title: inv.title || 'Orchestrated Investigation',
                        description: inv.description || '',
                        studies: [
                            {
                                identifier: sd.study?.id || 'study_orchestrated',
                                title: sd.study?.title || 'Main Study',
                                description: sd.study?.description || '',
                                assays: (sd.assays || []).map((assay: any) => ({
                                    identifier: assay.id,
                                    filename: assay.name || 'Assay',
                                    name: assay.name,
                                    description: assay.name, // Mapping name to description for now or create new field
                                    steps: assay.workflowSteps || [],
                                    measurementType: { term: 'N/A' },
                                    technologyType: { term: 'N/A' }
                                }))
                            }
                        ]
                    }
                    console.log("Hierarchy: ", hierarchy.value);
                    addLog({
                        timestamp: new Date().toISOString(),
                        level: 'INFO',
                        message: `Orchestration complete. ISA extracted.`
                    })
                }

                // Store Generated Code (Optional: could store in a new state variable)
                if (data.result.generated_code) {
                    addLog({
                        timestamp: new Date().toISOString(),
                        level: 'INFO',
                        message: `Generated Artifacts: ${Object.keys(data.result.generated_code).join(', ')}`
                    })
                }

            } else {
                throw new Error(data.message || 'Orchestration failed')
            }

        } catch (err: any) {
            console.error('Orchestration failed:', err)
            error.value = err.response?.data?.detail || err.message || 'Orchestration failed'

            addLog({
                timestamp: new Date().toISOString(),
                level: 'ERROR',
                message: `Orchestration failed: ${error.value}`
            })

            // No fallback to mock data - we want to see the real error in this new flow
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
        clientId,
        initWebSocket,
    }
})
