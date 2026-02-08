import api from './api';

export interface RunVeriflowResponse {
    run_id: string;
    status: string;
    message: string;
}

export const veriflowApi = {
    runVeriflow: (pdfFile: File, contextFile?: File) => {
        const formData = new FormData();
        formData.append('pdf_file', pdfFile);
        if (contextFile) {
            formData.append('context_file', contextFile);
        }
        return api.post<RunVeriflowResponse>('/veriflow/run', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },

    connectToWebSocket: (runId: string, onMessage: (event: any) => void) => {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ws/veriflow/${runId}`;
        
        const socket = new WebSocket(wsUrl);

        socket.onmessage = (event) => {
            onMessage(JSON.parse(event.data));
        };

        socket.onerror = (error) => {
            console.error('WebSocket Error:', error);
        };

        return socket;
    }
};
