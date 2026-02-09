import sys
import os
import json
import time
import asyncio

# Helper to set up environment
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, '..'))
project_root = os.path.abspath(os.path.join(backend_dir, '..'))

# 1. Set CWD to backend so config.yaml and prompts.yaml are found
os.chdir(backend_dir)

# 2. Add backend to sys.path
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import dotenv
dotenv.load_dotenv(os.path.join(project_root, '.env'))

from app.agents.scholar import ScholarAgent

async def run_multimodal_benchmark():
    # 1. Setup V2 Agent
    agent = ScholarAgent()
    
    # Construct path relative to this script to ensure it works from any CWD
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(script_dir, "mamamiaworkflow.pdf")
    # pdf_path = r"tests\978-3-031-94562-5_34.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found. Please place it in this directory.")
        return

    # 2. Test Configuration
    target_model = "gemini-3-pro-preview" 

    print(f"\n=== Starting Test ===")
    print(f"File: {pdf_path}")
    print(f"Model: {target_model}")
    
    # Configure the internal client directly with the string name
    # The new Client architecture handles authentication and connection internally
    agent.client.model_name = target_model
    
    # Ensure the correct prompt version is used
    agent.prompt_version = "v2_standard"

    start_time = time.time()
    
    try:
        # 3. Execute Analysis
        print("\n>> Uploading and Analyzing (Schema Enforced)...")
        
        # The agent now returns a clean dictionary derived from the Pydantic model
        output = await agent.analyze_publication(
            pdf_path=pdf_path,
            context_content="Focus on the data preprocessing pipeline steps.",
            upload_id="bench_v2_new_sdk"
        )
        
        duration = time.time() - start_time
        
        # 4. Validation
        if output.get("error"):
            print(f"\nFAILED: {output['error']}")
        else:
            isa = output.get("isa_json", {})
            tools = output.get("identified_tools", [])
            thoughts = output.get("agent_thoughts", None) # New "Thinking" field
            
            print(f"\nSUCCESS in {duration:.2f}s")
            
            # --- PRINT REASONING TRACE (New Feature) ---
            if thoughts:
                print(f"\n--- Agent Thoughts (Chain of Thought) ---")
                # Print first 500 chars or full thought if short
                preview = thoughts[:1000] + "..." if len(thoughts) > 1000 else thoughts
                print(preview)
                print("-" * 40)
            
            print(f"\nInvestigation: {isa.get('title', 'Unknown')[:50]}...")
            print(f"Tools Identified: {len(tools)}")
            
            # --- STRUCTURED OUTPUT PRINTING ---
            # With Pydantic Schema, tools are guaranteed to be in the format defined in schemas.py
            # (e.g., List[str])
            for t in tools:
                print(f" - {t}")

            out_file = f"result_benchmark_{os.path.basename(pdf_path)}.json"
            with open(out_file, "w") as f:
                json.dump(output, f, indent=2)
            print(f"\nSaved full output to {out_file}")

    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_multimodal_benchmark())