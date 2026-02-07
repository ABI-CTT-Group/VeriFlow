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


    function addMessage(message: Omit<Message, 'id' | 'timestamp'>) {
        messages.value.push({
            id: Date.now().toString(),
            timestamp: new Date(),
            ...message
        })
    }

    function sendMessage(content: string) {
        if (!content.trim()) return

        addMessage({
            type: 'user',
            content
        })

        // Simulate agent response
        setTimeout(() => {
            addMessage({
                type: 'agent',
                agent: 'reviewer',
                content: 'I understand your request. Processing...'
            })
        }, 1000)
    }

    return {
        messages,
        input,
        addMessage,
        sendMessage
    }
})
