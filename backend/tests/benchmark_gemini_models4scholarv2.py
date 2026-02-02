import sys
import os
import json
import time
import asyncio
import google.generativeai as genai

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.scholar_v2 import ScholarAgentV2

def get_gemini_models():
    """Dynamically fetch all models supporting content generation."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY not found.")
            return []
        
        genai.configure(api_key=api_key)
        valid_models = []
        print("\nScanning for available Gemini models...")
        for m in genai.list_models():
            # Check capabilities and name convention
            if 'generateContent' in m.supported_generation_methods:
                if "gemini" in m.name.lower():
                    # Strip 'models/' prefix if present for cleaner usage/filenames
                    clean_name = m.name.replace("models/", "")
                    valid_models.append(clean_name)
                    print(f" - Found: {clean_name}")
        return valid_models
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

async def run_multimodal_benchmark():
    # 1. Setup V2 Agent
    agent = ScholarAgentV2()
    
    # Target PDF - Ensure this matches your actual file
    pdf_path = r"tests\mamamiaworkflow.pdf" 
    # pdf_path = r"tests\978-3-031-94562-5_34.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found. Please place it in this directory.")
        return

    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]

    # 2. Get All Models
    target_models = get_gemini_models()
    
    if not target_models:
        print("No Gemini models found. Check API key or connection.")
        return

    print(f"\n=== Starting Comprehensive V2 Benchmark ===")
    print(f"Target File: {pdf_basename}")
    print(f"Models to Test: {len(target_models)}")
    
    results_summary = []

    # 3. Iterate through models
    for i, model_name in enumerate(target_models):
        print(f"\n------------------------------------------------")
        print(f"Testing Model [{i+1}/{len(target_models)}]: {model_name}")
        
        # Configure Agent dynamically
        # The client will handle retries for Rate Limits (429) automatically
        agent.client.model_name = model_name
        agent.prompt_version = "v2_multimodal"

        start_time = time.time()
        success = False
        error_msg = None
        tool_count = 0
        
        try:
            print(f">> Uploading and Analyzing (Smart Cache Active)...")
            
            # This call handles: Hash Check -> Cache Hit? -> Upload -> Generate
            output = await agent.analyze_publication(
                pdf_path=pdf_path,
                context_content="Focus on the data preprocessing pipeline steps.",
                upload_id=f"bench_{pdf_basename}_{model_name}"
            )
            
            duration = time.time() - start_time
            
            # Validate Output
            if output.get("error"):
                error_msg = output['error']
                print(f"FAILED: {error_msg}")
            else:
                success = True
                isa = output.get("isa_json", {})
                tools = output.get("identified_tools", [])
                tool_count = len(tools)
                
                print(f"SUCCESS in {duration:.2f}s")
                print(f"Investigation: {isa.get('title', 'Unknown')[:50]}...")
                print(f"Tools Identified: {tool_count}")

                # Save Full Result
                # Filename format: result_{pdf_base}_{model_safe}.json
                safe_model_name = model_name.replace("/", "_").replace(":", "")
                out_file = f"result_{pdf_basename}_{safe_model_name}.json"
                
                with open(out_file, "w") as f:
                    json.dump(output, f, indent=2)
                print(f"Saved output to: {out_file}")

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            print(f"CRITICAL ERROR: {e}")

        # Add to Summary
        results_summary.append({
            "model": model_name,
            "success": success,
            "duration_sec": round(duration, 2),
            "tools_found": tool_count,
            "error": error_msg
        })

        # Safety Sleep between models (Supplemental to Client's RateLimiter)
        # This helps clear the TPM window slightly before switching models
        time.sleep(120)

    # 4. Final Report
    print("\n\n=== BENCHMARK COMPLETE SUMMARY ===")
    print(f"{'Model':<35} | {'Time':<6} | {'Tools':<5} | {'Status'}")
    print("-" * 70)
    for res in results_summary:
        status = "OK" if res['success'] else "FAIL"
        print(f"{res['model']:<35} | {res['duration_sec']:<6} | {res['tools_found']:<5} | {status}")
        if not res['success']:
            print(f"   -> Error: {res.get('error')}")

if __name__ == "__main__":
    asyncio.run(run_multimodal_benchmark())