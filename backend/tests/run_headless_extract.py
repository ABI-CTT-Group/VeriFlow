import asyncio
import uuid
import sys
import os
import json
from pathlib import Path

# Ensure backend directory is in path so imports work
backend_path = Path(__file__).parent.parent
project_root = backend_path.parent
sys.path.append(str(backend_path))

from app.graph.workflow import app_graph
from app.state import AgentState

import dotenv
dotenv.load_dotenv(os.path.join(project_root, '.env'))

async def main():
    print("--- VeriFlow Headless Runner & Artifact Extractor ---")
    
    # 1. Configuration
    base_dir = backend_path
    pdf_path = str(base_dir / "tests" / "mamamiaworkflow.pdf") 
    repo_path = str(base_dir / "examples" / "mama-mia")
    output_base_dir = Path("output")

    # Reload prompts with absolute path
    from app.services.prompt_manager import prompt_manager
    prompts_path = base_dir / "prompts.yaml"
    if prompts_path.exists():
        print(f"Reloading prompts from: {prompts_path}")
        prompt_manager.load_prompts(str(prompts_path))

    if not os.path.exists(pdf_path) or not os.path.exists(repo_path):
        print(f"Error: PDF or Repo path missing.")
        return

    run_id = str(uuid.uuid4())[:8]
    run_output_dir = output_base_dir / run_id
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
        
        # 4. Extract and Save Artifacts
        raw_output = final_state.get('generated_code', {})
        
        if isinstance(raw_output, str):
            try:
                clean_json = raw_output.strip().removeprefix("```json").removesuffix("```").strip()
                raw_output = json.loads(clean_json)
            except Exception as e:
                print(f"Warning: Could not parse generated_code string as JSON: {e}")

        # Map to the INFRASTRUCTURE_CODE key used in v3_standard
        generated_data = raw_output.get("INFRASTRUCTURE_CODE", raw_output) if isinstance(raw_output, dict) else {}

        if generated_data:
            run_output_dir.mkdir(parents=True, exist_ok=True)
            print(f"Saving artifacts to: {run_output_dir}")

            # 1. Save Mapping Logic
            if "mapping_logic" in generated_data:
                with open(run_output_dir / "mapping.txt", "w", encoding="utf-8") as f:
                    f.write(str(generated_data["mapping_logic"]))
                print(f"  [+] Saved mapping.txt")

            # 2. Save Workflow & Job files (Fixed logic for nested dict)
            if "workflow" in generated_data:
                workflow_data = generated_data["workflow"]
                if isinstance(workflow_data, dict):
                    for filename, content in workflow_data.items():
                        with open(run_output_dir / filename, "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"  [+] Saved {filename}")
                else:
                    with open(run_output_dir / "main_workflow.cwl", "w", encoding="utf-8") as f:
                        f.write(str(workflow_data))
                    print(f"  [+] Saved main_workflow.cwl")
                
            # 3. Save Components (e.g., Component 1, Component 2)
            # v3_standard uses a list of dicts for components
            components = generated_data.get("components", [])
            if isinstance(components, list):
                for component in components:
                    step_name = component.get("step_name", "UnknownStep").replace(" ", "_")
                    files = component.get("files", {})
                    
                    comp_dir = run_output_dir / step_name
                    comp_dir.mkdir(exist_ok=True)
                    
                    for filename, code in files.items():
                        with open(comp_dir / filename, "w", encoding="utf-8") as f:
                            f.write(code)
                    print(f"  [+] Saved files for {step_name}")

        else:
            print("No code artifacts found in the final state.")

        print(f"\nProcessing complete. Artifacts in output/{run_id}/")
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())