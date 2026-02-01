import sys
import os
import json
import time
import asyncio

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.scholar_v2 import ScholarAgentV2

async def run_multimodal_benchmark():
    # 1. Setup V2 Agent
    agent = ScholarAgentV2()
    
    pdf_path = r"tests\mamamiaworkflow.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found. Please place it in this directory.")
        return

    # 2. Test Configuration
    test_case = {
        # Using the exact model you saw success with
        "model": "gemini-2.5-flash-preview-09-2025", 
        "version": "v2_multimodal"
    }

    print(f"\n=== Starting V2 (Multimodal) Benchmark ===")
    print(f"File: {pdf_path}")
    print(f"Model: {test_case['model']}")
    
    # Force client to use this specific model
    agent.client.model_name = test_case['model']
    import google.generativeai as genai
    agent.client.model = genai.GenerativeModel(
        model_name=test_case['model'],
        safety_settings=agent.client.SAFETY_SETTINGS
    )
    
    agent.prompt_version = test_case['version']

    start_time = time.time()
    
    try:
        # 3. Execute Analysis
        print("\n>> Uploading and Analyzing...")
        output = await agent.analyze_publication(
            pdf_path=pdf_path,
            context_content="Focus on the data preprocessing pipeline steps.",
            upload_id="bench_v2_001"
        )
        
        duration = time.time() - start_time
        
        # 4. Validation
        if output.get("error"):
            print(f"\nFAILED: {output['error']}")
        else:
            isa = output.get("isa_json", {})
            tools = output.get("identified_tools", [])
            print(f"\nSUCCESS in {duration:.2f}s")
            print(f"Investigation: {isa.get('title', 'Unknown')[:50]}...")
            print(f"Tools Identified: {len(tools)}")
            
            # --- ROBUST PRINTING LOOP ---
            for t in tools:
                if isinstance(t, dict):
                    # It's a proper object: {"name": "ToolName", ...}
                    print(f" - {t.get('name', 'Unknown')}: {t.get('description', '')[:40]}...")
                elif isinstance(t, str):
                    # It's just a string (Model hallucinated schema): "ToolName"
                    print(f" - [String Only]: {t}")
                else:
                    print(f" - [Unknown Format]: {str(t)}")

            out_file = f"result_v2_benchmark.json"
            with open(out_file, "w") as f:
                json.dump(output, f, indent=2)
            print(f"\nSaved full output to {out_file}")

    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_multimodal_benchmark())