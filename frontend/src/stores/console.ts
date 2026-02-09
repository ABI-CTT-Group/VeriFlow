import { defineStore } from 'pinia'
import { ref } from 'vue'
import { wsService } from '../services/websocket'

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
            timestamp: new Date()
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

    function sendMessage(content: string, agent?: string) {
        if (!content.trim()) return

        // 1. Add to local store (optimistic UI)
        addMessage({
            type: 'user',
            content,
            agent: agent as any, // Store target agent if any
            timestamp: new Date()
        })

        // 2. Send to backend
        wsService.send({
            type: 'user_message',
            content,
            agent: agent || 'system'
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
