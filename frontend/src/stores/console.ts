import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Message {
    id: string
    type: 'user' | 'agent' | 'system'
    agent?: 'scholar' | 'engineer' | 'reviewer'
    content: string
    timestamp: Date
}

export const useConsoleStore = defineStore('console', () => {
    const messages = ref<Message[]>([
        {
            id: '1',
            type: 'system',
            content: 'VeriFlow initialized. Agents ready.',
            timestamp: new Date(Date.now() - 300000)
        },
        {
            id: '2',
            type: 'agent',
            agent: 'scholar',
            content: 'Analyzing PDF: breast_cancer_segmentation.pdf...',
            timestamp: new Date(Date.now() - 240000)
        },
        {
            id: '3',
            type: 'agent',
            agent: 'scholar',
            content: 'Extracted ISA hierarchy: 1 Investigation, 1 Study, 2 Assays. Creating SDS metadata...',
            timestamp: new Date(Date.now() - 180000)
        },
        {
            id: '4',
            type: 'agent',
            agent: 'scholar',
            content: 'Identified measurements: DCE-MRI Scans (384 subjects), Tools: nnU-Net, Models: Pretrained weights',
            timestamp: new Date(Date.now() - 120000)
        },
        {
            id: '5',
            type: 'agent',
            agent: 'reviewer',
            content: 'Validation complete. Study design populated. Ready for workflow assembly.',
            timestamp: new Date(Date.now() - 60000)
        }
    ])

    const input = ref('')


    function addMessage(message: Partial<Message> & { content: string, type: Message['type'] }) {
        messages.value.push({
            id: message.id || Date.now().toString(),
            timestamp: message.timestamp || new Date(),
            ...message
        })
    }

    function sendMessage(content: string) {
        if (!content.trim()) return

        addMessage({
            type: 'user',
            content,
            timestamp: new Date()
        })
    }

    // Handle streaming chunks from agents
    // We keep track of the last streaming message to append chunks
    const lastStreamMessageId = ref<string | null>(null)

    function appendAgentMessage(agent: string, chunk: string) {
        // Enforce lowercase for styling matching
        const normalizedAgent = agent.toLowerCase()

        // If we have a current streaming message for this agent, append to it
        if (lastStreamMessageId.value) {
            const msgIndex = messages.value.findIndex(m => m.id === lastStreamMessageId.value)
            if (msgIndex !== -1 && messages.value[msgIndex].agent === normalizedAgent) {
                messages.value[msgIndex].content += chunk
                return
            }
        }

        // define new message
        const newId = Date.now().toString()
        addMessage({
            id: newId,
            type: 'agent',
            agent: normalizedAgent as any, // Cast to agent type
            content: chunk,
            timestamp: new Date()
        })
        lastStreamMessageId.value = newId
    }

    function addSystemMessage(content: string) {
        // Reset stream tracking on system message (status update)
        lastStreamMessageId.value = null

        addMessage({
            type: 'system',
            content,
            timestamp: new Date()
        })
    }

    return {
        messages,
        input,
        addMessage,
        sendMessage,
        appendAgentMessage,
        addSystemMessage
    }


})
