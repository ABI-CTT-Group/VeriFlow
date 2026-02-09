import asyncio
import websockets
import json
import requests
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"
PDF_PATH = "C:/Users/lgao142/Desktop/AI Agent 2026/a-google-hackathon/VeriFlow/backend/tests/sample_data/example.pdf" # Adjust path as needed
REPO_PATH = "C:/Users/lgao142/Desktop/AI Agent 2026/a-google-hackathon/VeriFlow/backend" # Adjust path as needed

async def test_websocket_streaming():
    client_id = f"test-client-{uuid.uuid4()}"
    uri = f"{WS_URL}/{client_id}"

    print(f"Connecting to WebSocket: {uri}")
    
    async with websockets.connect(uri) as websocket:
        print("WebSocket Connected!")

        # Trigger Orchestration
        payload = {
            "pdf_path": PDF_PATH,
            "repo_path": REPO_PATH,
            "client_id": client_id
        }
        
        print(f"Sending orchestration request to {BASE_URL}/api/v1/orchestrate")
        try:
            # Send request in a separate task/thread to not block the event loop
            import threading
            def send_request():
                try:
                    res = requests.post(f"{BASE_URL}/api/v1/orchestrate", json=payload)
                    print(f"Orchestration Status: {res.status_code}")
                    print(f"Orchestration Response: {res.text[:200]}...")
                except Exception as e:
                    print(f"Request failed: {e}")

            threading.Thread(target=send_request, daemon=True).start()
        except Exception as e:
            print(f"Error triggering orchestration: {e}")

        print("Listening for messages... (Ctrl+C to stop)")
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"\n[WS Received]: {json.dumps(data, indent=2)}")
                
                if data.get("type") == "status_update" and data.get("status") == "completed":
                     # Check if it is the final reviewer completion or just a step
                     if "Reviewer Agent" in data.get("message", ""):
                         print("Workflow likely finished.")
                         break

        except websockets.ConnectionClosed:
            print("WebSocket connection closed")

if __name__ == "__main__":
    # Create sample PDF if not exists for testing purposes
    import os
    if not os.path.exists(PDF_PATH):
        print(f"Sample PDF not found at {PDF_PATH}. Please provide a valid path or create a dummy file.")
        # Create dummy file
        os.makedirs(os.path.dirname(PDF_PATH), exist_ok=True)
        with open(PDF_PATH, 'w') as f:
            f.write("Dummy PDF content")

    try:
        asyncio.run(test_websocket_streaming())
    except KeyboardInterrupt:
        print("Test stopped.")
