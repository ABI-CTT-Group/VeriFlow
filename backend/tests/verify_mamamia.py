
import asyncio
import aiohttp
import json
import uuid
import sys

BACKEND_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def verify_mamamia():
    client_id = str(uuid.uuid4())
    print(f"Client ID: {client_id}")
    
    async with aiohttp.ClientSession() as session:
        # 1. Connect WebSocket
        ws_url = f"{WS_URL}/ws/{client_id}"
        print(f"Connecting to WebSocket: {ws_url}")
        
        async with session.ws_connect(ws_url) as ws:
            print("WebSocket connected.")
            
            # 2. Call HTTP Endpoint
            api_url = f"{BACKEND_URL}/api/v1/mama-mia-cache?client_id={client_id}"
            print(f"Calling API: {api_url}")
            
            async with session.get(api_url) as response:
                print(f"API Status: {response.status}")
                if response.status != 200:
                    print("API Failed:", await response.text())
                    return
                
                data = await response.json()
                print("API Response keys:", list(data.keys()))
                if "result" in data:
                    print("Result keys:", list(data["result"].keys()))
                    if "isa_json" in data["result"]:
                         print("PASS: Got 'isa_json' in response.")
                    else:
                         print("FAIL: Missing 'isa_json'.")
                else:
                    print("FAIL: Missing 'result'.")

            # 3. Listen for WebSocket messages
            print("Listening for WebSocket messages...")
            agents_seen = set()
            try:
                while True:
                    msg = await asyncio.wait_for(ws.receive(), timeout=15.0)
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("type") == "status_update":
                            content = data.get("message", "")
                            # Identify agent
                            if "Scholar Agent" in content: agents_seen.add("Scholar")
                            if "Engineer Agent" in content: agents_seen.add("Engineer")
                            if "Reviewer Agent" in content: agents_seen.add("Reviewer")
                            
                            print(f"Received: {content[:50]}...")
                            
                            if len(agents_seen) >= 3:
                                print(f"PASS: Seen messages from {agents_seen}")
                                break
                                
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print('ws connection closed with exception %s', ws.exception())
                        break
            except asyncio.TimeoutError:
                print("WebSocket timeout.")
            
            if len(agents_seen) > 0:
                print(f"Partial PASS: Seen agents {agents_seen}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_mamamia())
