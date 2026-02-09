/**
 * WebSocket Service
 * Handles real-time communication with the backend.
 */

type MessageHandler = (data: any) => void

class WebSocketService {
    private socket: WebSocket | null = null
    private handlers: Record<string, MessageHandler[]> = {}
    private isConnectedInternal = false
    private clientId = null as string | null

    get isConnected() {
        return this.isConnectedInternal
    }

    getClientId() {
        return this.clientId
    }

    constructor() {
        this.handlers = {
            'status_update': [],
            'agent_stream': [],
            'error': []
        }
    }

    /**
     * Connect to the WebSocket server
     * @param clientId Unique client ID
     * @param url WebSocket URL (defaults to localhost:8000/ws/{clientId})
     */
    connect(clientId: string, url?: string): Promise<void> {
        return new Promise((resolve, reject) => {
            if (this.socket && this.isConnected && this.clientId === clientId) {
                resolve()
                return
            }

            this.disconnect()
            this.clientId = clientId

            // Determine WS URL

            // In Docker/Production this might need adjustment, but for now we assume localhost or relative to API
            // const wsUrl = url || `ws://localhost:8000/ws/${clientId}`
            // Use window.location to determine the host and protocol (ws/wss)
            // This works for both:
            // - Local dev (via Vite proxy): ws://localhost:5173/ws/... -> proxies to localhost:8000
            // - Production/Cloud: wss://domain.com/ws/... -> goes to Nginx -> backend
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
            const host = window.location.host // Includes port if present
            const wsUrl = url || `${protocol}//${host}/ws/${clientId}`

            console.log(`Connecting to WebSocket: ${wsUrl}`)

            try {
                this.socket = new WebSocket(wsUrl)

                this.socket.onopen = () => {
                    console.log('WebSocket Connected')
                    this.isConnectedInternal = true
                    resolve()
                }

                this.socket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data)
                        this.handleMessage(data)
                    } catch (err) {
                        console.error('Failed to parse WS message:', err)
                    }
                }

                this.socket.onerror = (error) => {
                    console.error('WebSocket Error:', error)
                    this.notifyHandlers('error', { message: 'Connection error' })
                    // Don't reject here necessarily as connection might recover or it's a runtime error
                }

                this.socket.onclose = () => {
                    console.log('WebSocket Disconnected')
                    this.isConnectedInternal = false
                    this.clientId = null
                }
            } catch (err) {
                reject(err)
            }
        })
    }

    disconnect() {
        if (this.socket) {
            this.socket.close()
            this.socket = null
        }
        this.isConnectedInternal = false
        this.clientId = null
    }

    /**
     * Subscribe to a specific message type
     */
    on(type: string, handler: MessageHandler) {
        if (!this.handlers[type]) {
            this.handlers[type] = []
        }
        this.handlers[type].push(handler)
    }

    /**
     * Unsubscribe from a specific message type
     */
    off(type: string, handler: MessageHandler) {
        if (!this.handlers[type]) return

        const index = this.handlers[type].indexOf(handler)
        if (index !== -1) {
            this.handlers[type].splice(index, 1)
        }
    }

    private handleMessage(data: any) {
        // console.log('WS Message:', data)
        const type = data.type

        if (type && this.handlers[type]) {
            this.handlers[type].forEach(handler => handler(data))
        }
    }

    private notifyHandlers(type: string, data: any) {
        if (this.handlers[type]) {
            this.handlers[type].forEach(handler => handler(data))
        }
    }

    /**
     * Send a message to the backend
     */
    send(data: any) {
        if (this.socket && this.isConnected) {
            this.socket.send(JSON.stringify(data))
        } else {
            console.warn('Cannot send message: WebSocket not connected')
            this.notifyHandlers('error', { message: 'Cannot send: WebSocket disconnected' })
        }
    }
}

// Export singleton
export const wsService = new WebSocketService()
