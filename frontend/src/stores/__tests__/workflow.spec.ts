import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWorkflowStore } from '../workflow'

describe('Workflow Store', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
    })

    it('initializes with empty state', () => {
        const store = useWorkflowStore()
        expect(store.nodes).toEqual([])
        expect(store.edges).toEqual([])
        expect(store.isLoading).toBe(false)
    })

    it('can add nodes', () => {
        const store = useWorkflowStore()
        const node = {
            id: 'n1',
            type: 'custom',
            position: { x: 0, y: 0 },
            data: { label: 'Node 1' }
        }

        // Assuming there's an action or direct state mutation
        // Ideally we should test actions, but let's test state reactivity first
        store.nodes.push(node)

        expect(store.nodes).toHaveLength(1)
        expect(store.nodes[0].id).toBe('n1')
    })

    it('selects a node', () => {
        const store = useWorkflowStore()
        const node = {
            id: 'n1',
            type: 'custom',
            position: { x: 0, y: 0 },
            data: { label: 'Node 1' }
        }
        store.nodes.push(node as any)

        store.selectedNode = 'n1'
        expect(store.selectedNode).toBe('n1')
    })
})
