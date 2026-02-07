import sys
import os
import json
import time
import asyncio
from pathlib import Path
from google import genai

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.scholar_v2 import ScholarAgentV2

def get_gemini_models():
    """
    Dynamically fetch all models using the new Google Gen AI SDK (v2).
    Filters for models likely to support the new features.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY not found.")
            return []
        
        # New SDK Client
        client = genai.Client(api_key=api_key)
        
        valid_models = []
        print("\nScanning for available Gemini models (SDK v2)...")
        
        # client.models.list() returns an iterator of model objects
        for m in client.models.list():
            name = m.name.replace("models/", "")
            
            # Filter for Gemini models that likely support content generation
            # Note: Specific capability checks are less explicit in v2 list results,
            # so we rely on naming conventions for the benchmark.
            if "gemini" in name.lower() and "vision" not in name.lower():
                valid_models.append(name)
                print(f" - Found: {name}")
                
        # prioritize 2.0 models
        valid_models.sort(key=lambda x: "2.0" in x, reverse=True)
        return valid_models

    except Exception as e:
        print(f"Error listing models: {e}")
        # Fallback list if enumeration fails
        return ["gemini-2.0-flash", "gemini-1.5-pro"]

async def run_multimodal_benchmark():
    # 1. Setup Environment
    # Define and create the benchmark directory
    benchmark_dir = Path(r"D:\Temp\VeriFlowD\benchmarkruns")
    benchmark_dir.mkdir(exist_ok=True)
    print(f"Output Directory: {benchmark_dir.resolve()}")

    agent = ScholarAgentV2()
    
    # Target PDF
    pdf_path = r"tests\mamamiaworkflow.pdf"
    # pdf_path = r"tests\978-3-031-94562-5_34.pdf"
    if not os.path.exists(pdf_path):
        # Fallback for flexibility
        pdf_path = r"tests\mamamiaworkflow.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: No test PDF found at {pdf_path}")
        return

    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]

    # 2. Get Models
    target_models = get_gemini_models()
    if not target_models:
        print("No models found.")
        return

    print(f"\n=== Starting Comprehensive V2 Benchmark (Structured Output) ===")
    print(f"Target File: {pdf_basename}")
    print(f"Models to Test: {len(target_models)}")
    
    results_summary = []

    # 3. Iterate through models
    for i, model_name in enumerate(target_models):
        print(f"\n------------------------------------------------")
        print(f"Testing Model [{i+1}/{len(target_models)}]: {model_name}")
        
        # Configure Agent dynamically
        agent.client.model_name = model_name
        agent.prompt_version = "v2_multimodal"

        start_time = time.time()
        success = False
        error_msg = None
        tool_count = 0
        thoughts_preview = "N/A"
        
        try:
            print(f">> Uploading and Analyzing...")
            
            # Execute Analysis
            output = await agent.analyze_publication(
                pdf_path=pdf_path,
                context_content="Focus on the data preprocessing pipeline steps.",
                upload_id=f"bench_{model_name}"
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
                thoughts = output.get("agent_thoughts", "")
                
                print(f"SUCCESS in {duration:.2f}s")
                
                # Show thoughts if available
                if thoughts:
                    thoughts_preview = thoughts[:100] + "..."
                    print(f"Thoughts: {thoughts_preview}")
                    
                print(f"Investigation: {isa.get('title', 'Unknown')[:50]}...")
                print(f"Tools Identified: {tool_count}")

                # Save Full Result to BENCHMARK folder
                safe_model_name = model_name.replace("/", "_").replace(":", "")
                out_filename = f"result_{pdf_basename}_{safe_model_name}.json"
                out_file_path = benchmark_dir / out_filename
                
                with open(out_file_path, "w", encoding='utf-8') as f:
                    json.dump(output, f, indent=2)
                print(f"Saved output to: {out_file_path}")

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
            "has_thoughts": bool(thoughts_preview != "N/A"),
            "error": error_msg
        })

        # Sleep to avoid Rate Limits
        print("Cooling down (30s)...")
        time.sleep(30)

    # 4. Final Report
    print("\n\n=== BENCHMARK COMPLETE SUMMARY ===")
    print(f"{'Model':<30} | {'Time':<6} | {'Tools':<5} | {'Thoughts'} | {'Status'}")
    print("-" * 80)
    for res in results_summary:
        status = "OK" if res['success'] else "FAIL"
        thought_mark = "Yes" if res['has_thoughts'] else "No"
        print(f"{res['model']:<30} | {res['duration_sec']:<6} | {res['tools_found']:<5} | {thought_mark:<8} | {status}")
        if not res['success']:
            print(f"   -> Error: {res.get('error')}")

if __name__ == "__main__":
    asyncio.run(run_multimodal_benchmark())