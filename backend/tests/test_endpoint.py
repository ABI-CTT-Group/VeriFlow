import requests
import json

BASE_URL = "http://localhost:8000"
PDF_PATH = "C:/Users/lgao142/Desktop/AI Agent 2026/a-google-hackathon/VeriFlow/backend/tests/sample_data/example.pdf"
REPO_PATH = "C:/Users/lgao142/Desktop/AI Agent 2026/a-google-hackathon/VeriFlow/backend"

payload = {
    "pdf_path": PDF_PATH,
    "repo_path": REPO_PATH,
    "client_id": "test-client"
}

try:
    print(f"Sending POST to {BASE_URL}/api/v1/orchestrate...")
    res = requests.post(f"{BASE_URL}/api/v1/orchestrate", json=payload, timeout=10)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text[:500]}")
except Exception as e:
    print(f"Request failed: {e}")
