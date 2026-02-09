import asyncio
import uuid
import sys
import os
from pathlib import Path
from pprint import pprint

# Ensure backend directory is in path so imports work
backend_path = Path(__file__).parent.parent
project_root = backend_path.parent
sys.path.append(str(backend_path))

from app.graph.workflow import app_graph
from app.state import AgentState

import dotenv
dotenv.load_dotenv(os.path.join(project_root, '.env'))
async def main():
    print("--- VeriFlow Headless Runner ---")
    
    # 1. Configuration (Edit these paths as needed for local testing)
    # Using relative paths assuming running from backend root or tests folder
    base_dir = backend_path
    pdf_path = str(base_dir / "tests" / "mamamiaworkflow.pdf") 
    repo_path = str(base_dir / "examples" / "mama-mia")

    # FIX: Reload prompts with absolute path to ensure they are found regardless of CWD
    from app.services.prompt_manager import prompt_manager
    prompts_path = base_dir / "prompts.yaml"
    if prompts_path.exists():
        print(f"Reloading prompts from: {prompts_path}")
        prompt_manager.load_prompts(str(prompts_path))
    else:
        print(f"Warning: Prompts file not found at {prompts_path}")

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return
    if not os.path.exists(repo_path):
        print(f"Error: Repo not found at {repo_path}")
        return

    run_id = str(uuid.uuid4())[:8]
    print(f"Run ID: {run_id}")
    
    # 2. Initialize State
    initial_state: AgentState = {
        "run_id": run_id,
        "pdf_path": pdf_path,
        "repo_path": repo_path,
        "isa_json": None,
        "repo_context": None,
        "generated_code": {},
        "validation_errors": [],
        "retry_count": 0,
        "review_decision": None,
        "review_feedback": None
    }
    
    print("Starting Graph Execution...")
    
    # 3. Invoke Graph
    try:
        final_state = await app_graph.ainvoke(initial_state)
        
        print("\n--- Execution Finished ---")
        print(f"Review Decision: {final_state.get('review_decision')}")
        print(f"Retry Count: {final_state.get('retry_count')}")
        
        if final_state.get('isa_json'):
            print(f"ISA JSON Extracted: Yes (Keys: {list(final_state['isa_json'].keys())})")
            
        generated_code = final_state.get('generated_code', {})
        print(f"Artifacts Generated: {list(generated_code.keys())}")
        
        print(f"\nFull logs available in: logs/{run_id}/")
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())