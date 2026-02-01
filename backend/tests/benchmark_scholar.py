import sys
import os
import json
import time
import asyncio
import google.generativeai as genai  # Required for listing models

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.scholar import ScholarAgent

def list_available_models():
    """Queries the Gemini API to find valid model names for this API Key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CRITICAL ERROR: GEMINI_API_KEY environment variable is not set.")
        return []

    genai.configure(api_key=api_key)
    
    print("\n=== AVAILABLE GEMINI MODELS ===")
    valid_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
                valid_models.append(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
    print("===============================\n")
    return valid_models

async def run_benchmark():
    
    # 2. Setup Agent
    agent = ScholarAgent()
    
    # Path to the PDF uploaded by user
    pdf_path = r"tests\mamamiaworkflow.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Warning: Test file {pdf_path} not found.")
        print("Creating dummy PDF text for syntax testing...")
        pdf_text = "This is a dummy scientific paper about MRI segmentation using U-Net."
    else:
        print(f"Reading and extracting text from {pdf_path}...")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_text = agent.extract_text_from_pdf(pdf_bytes)

    # 3. Define Test Matrix
    # UPDATE THESE NAMES based on the output from list_available_models()
    # Common valid names: 'models/gemini-2.5-flash', 'models/gemini-1.5-flash-latest'
    test_cases = [
        {"model": "models/gemini-3-flash-preview", "version": "v1_standard"}, 
        {"model": "models/gemini-2.0-flash", "version": "v1_standard"},
    ]

    print(f"\nStarting Benchmark on document (Length: {len(pdf_text)} chars)\n")

    results = []

    for case in test_cases:
        print(f"Testing Config: Model={case['model']}, Prompt={case['version']}...")
        start_time = time.time()
        
        # --- DYNAMIC CONFIGURATION INJECTION ---
        agent.prompt_version = case['version']
        
        # Fix: Ensure the internal Gemini client uses the test-case model
        # We also strip 'models/' prefix if it exists, as some SDK calls double it up
        model_name = case['model']
        if model_name.startswith("models/"):
             model_name = model_name.replace("models/", "")
             
        agent.gemini.model_name = model_name
        
        # Re-initialize the specific GenerativeModel object inside the client
        # This forces the client to use the new model immediately
        agent.gemini.model = genai.GenerativeModel(
            model_name=model_name,
            safety_settings=agent.gemini.SAFETY_SETTINGS
        )
        
        try:
            output = await agent.analyze_publication(
                pdf_text=pdf_text,
                context_content="Focus on the MRI segmentation methodology.",
                upload_id="benchmark_test_001"
            )
            
            duration = time.time() - start_time
            
            # Check for API errors captured by the agent
            if output.get("error"):
                raise Exception(f"Agent API Error: {output['error']}")

            # Handle potential NoneType if extraction failed completely
            isa_json = output.get("isa_json") or {}
            
            success = "investigation" in isa_json and isa_json["investigation"] is not None
            tools_count = len(output.get("identified_tools", []))
            
            # Calculate Confidence
            scores = output.get("confidence_scores", {})
            confidence_avg = 0
            if scores:
                vals = [v.get("value", 0) if isinstance(v, dict) else v for v in scores.values()]
                if vals:
                    confidence_avg = sum(vals) / len(vals)

            results.append({
                "config": case,
                "duration": round(duration, 2),
                "success": success,
                "tools_count": tools_count,
                "confidence_avg": round(confidence_avg, 2)
            })
            
            # Save output
            filename = f"results_scholar_{case['model'].replace('/','_')}_{case['version']}.json"
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)
                
        except Exception as e:
            print(f"FAILED: {e}")
            results.append({"config": case, "error": str(e)})

    # 4. Report
    print("\n=== Benchmark Summary ===")
    print(f"{'Model':<30} | {'Version':<15} | {'Time(s)':<8} | {'Success'}")
    print("-" * 80)
    for r in results:
        if "error" in r:
             print(f"{r['config']['model']:<30} | {r['config']['version']:<15} | ERROR: {r['error']}")
        else:
            print(f"{r['config']['model']:<30} | {r['config']['version']:<15} | {r['duration']:<8} | {r['success']}")

if __name__ == "__main__":
    # list_available_models()
    asyncio.run(run_benchmark())