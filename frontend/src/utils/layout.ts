import dagre from 'dagre'
import type { Node, Edge } from '@vue-flow/core'

const NODE_WIDTH = 280
const HEADER_HEIGHT = 60
const PORT_HEIGHT = 40
const BASE_PADDING = 20

/**
 * Calculates the estimated height of a node based on its data inputs/outputs.
 * This ensures the layout engine allocates enough space preventing overlap.
 */
const getNodeHeight = (node: Node) => {
    // If explicit style/dimensions exist, use them (not common in this setup yet)
    if (node.style && typeof node.style === 'object' && 'height' in node.style) {
        return parseInt((node.style as any).height)
    }

    // Estimate based on inputs/outputs
    // Each input/output is roughly 40px height + header + padding
    const inputs = node.data?.inputs?.length || 0
    const outputs = node.data?.outputs?.length || 0
    return HEADER_HEIGHT + Math.max(0, (inputs + outputs) * PORT_HEIGHT) + BASE_PADDING
}

/**
 * Applies a Dagre-based auto-layout to the given nodes and edges.
 * Returns a new array of nodes with updated positions.
 * 
 * @param nodes Array of Vue Flow nodes
 * @param edges Array of Vue Flow edges
 * @param direction 'LR' (Left-to-Right) or 'TB' (Top-to-Bottom)
 */
export const getLayoutedElements = (
    nodes: Node[],
    edges: Edge[],
    direction: 'LR' | 'TB' = 'LR'
): { nodes: Node[]; edges: Edge[] } => {
    const dagreGraph = new dagre.graphlib.Graph()

    dagreGraph.setDefaultEdgeLabel(() => ({}))

    dagreGraph.setGraph({
        rankdir: direction,
        align: 'DL', // Align top-left
        nodesep: 80, // Horizontal separation between nodes
        ranksep: 100, // Vertical separation between ranks (layers)
        marginx: 50,
        marginy: 50
    })

    // Add nodes to dagre
    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, {
            width: NODE_WIDTH,
            height: getNodeHeight(node)
        })
    })

    // Add edges to dagre
    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target)
    })

    // Calculate layout
    dagre.layout(dagreGraph)

    // Apply calculated positions back to nodes
    const layoutedNodes = nodes.map((node) => {
        const nodeWithPosition = dagreGraph.node(node.id)

        // Dagre returns center point, Vue Flow uses top-left
        // So we offset by half width/height
        const x = nodeWithPosition.x - (NODE_WIDTH / 2)
        const y = nodeWithPosition.y - (nodeWithPosition.height / 2)

        return {
            ...node,
            position: { x, y }
        }
    })

    return { nodes: layoutedNodes, edges }
}
