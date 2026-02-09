import asyncio
import uuid
import sys
import os
import json
from pathlib import Path
from pprint import pprint

# --- Setup Paths ---
# Ensure backend directory is in path so imports work
backend_path = Path(__file__).parent.parent
project_root = backend_path.parent
sys.path.append(str(backend_path))

import dotenv
dotenv.load_dotenv(os.path.join(project_root, '.env'))

# Import the new Factory function
from app.graph.workflow import create_workflow
from app.state import AgentState
from app.services.prompt_manager import prompt_manager

async def main():
    print("--- VeriFlow Headless Runner: Plan & Apply Pattern ---\n")
    
    # 1. Configuration
    # Adjust these paths to point to your actual test files
    base_dir = backend_path
    pdf_path = str(base_dir / "tests" / "mamamiaworkflow.pdf") 
    repo_path = str(base_dir / "examples" / "mama-mia")
    
    # Reload prompts to ensure latest version
    prompts_path = base_dir / "prompts.yaml"
    if prompts_path.exists():
        prompt_manager.load_prompts(str(prompts_path))

    if not os.path.exists(pdf_path) or not os.path.exists(repo_path):
        print("Error: Test files not found. Please check paths.")
        return

    run_id = str(uuid.uuid4())[:8]
    print(f"Run ID: {run_id}")

    # ==========================================
    # PHASE 1: Initial Execution (Standard)
    # ==========================================
    print("\n[Phase 1] Starting Initial Workflow (Scholar -> End)...")
    
    initial_state: AgentState = {
        "run_id": run_id,
        "pdf_path": pdf_path,
        "repo_path": repo_path,
        "user_context": "We will use cpu for executing nnunet.",
        "isa_json": None,
        "repo_context": None,
        "generated_code": {},
        "validation_errors": [],
        "retry_count": 0,
        "review_decision": None,
        "review_feedback": None,
        "agent_directives": {} # Empty initially
    }

    # Create graph starting at default entry point
    workflow_v1 = create_workflow(entry_point="scholar")
    
    # Run Phase 1
    try:
        state_after_run1 = await workflow_v1.ainvoke(initial_state)
        print("[Phase 1] Complete.")
        print(f"Initial Review Decision: {state_after_run1.get('review_decision')}")
        
        # Visualize initial output (Engineer's code)
        code = state_after_run1.get('generated_code', {})
        print(f"Generated Artifacts: {list(code.keys())}")

    except Exception as e:
        print(f"Phase 1 Failed: {e}")
        return

    # ==========================================
    # PHASE 2: Human Intervention (Plan)
    # ==========================================
    print("\n[Phase 2] Simulating Human Intervention (Chat & Plan)...")
    
    # Simulate user chatting with Engineer and giving a directive
    user_directive = "The Dockerfile base image must be 'python:3.11-alpine' specifically."
    print(f"User Directive: '{user_directive}'")
    
    # Update state:
    # 1. Carry over everything from Run 1
    # 2. Inject directive
    # 3. Reset validation/review status so it processes fresh
    state_for_restart = state_after_run1.copy()
    state_for_restart["agent_directives"] = {"engineer": user_directive}
    state_for_restart["validation_errors"] = [] 
    state_for_restart["review_decision"] = None
    state_for_restart["retry_count"] = 0 # Optional: reset retries or keep them

    # ==========================================
    # PHASE 3: Apply & Restart (Apply)
    # ==========================================
    print(f"\n[Phase 3] Restarting Workflow from 'Engineer' Node...")
    
    # Create graph STARTING at 'engineer'
    # This bypasses Scholar (saving time/cost) but uses Scholar's data from state_for_restart
    workflow_v2 = create_workflow(entry_point="engineer")
    
    try:
        final_state = await workflow_v2.ainvoke(state_for_restart)
        
        print("\n[Phase 3] Execution Finished.")
        print("--------------------------------------------------")
        
        # Verification
        # Check if the directive was actually applied in the generated code
        gen_code = final_state.get("generated_code", {})
        dockerfile = gen_code.get("dockerfile", "") or gen_code.get("Dockerfile", "") # Handle key variations
        
        print("Verifying Directive Application...")
        if "python:3.11-alpine" in str(dockerfile):
            print("✅ SUCCESS: Directive applied! Found 'python:3.11-alpine' in Dockerfile.")
        else:
            print("❌ FAILURE: Directive NOT applied. Dockerfile content snippet:")
            print(str(dockerfile)[:500])
            
        print(f"Final Review Decision: {final_state.get('review_decision')}")
        print(f"Full logs: logs/{run_id}/")

    except Exception as e:
        print(f"Phase 3 Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())