"""
VeriFlow Service
This service encapsulates the logic for running the VeriFlow langraph workflow.
"""
import logging
import shutil
from pathlib import Path
from typing import Optional, Callable, Any

from app.graph.workflow import app_graph
from app.state import AgentState

logger = logging.getLogger(__name__)

class VeriFlowService:
    """
    Service for running the VeriFlow langraph workflow.
    """
    async def run_workflow(
        self,
        run_id: str,
        pdf_path: Path,
        repo_path: Path,
        stream_callback: Optional[Callable[[str, Any], None]] = None,
        temp_dir: Optional[Path] = None,
    ):
        """
        Run the VeriFlow langraph workflow.

        :param run_id: The ID of the run.
        :param pdf_path: The path to the PDF file.
        :param repo_path: The path to the repository.
        :param stream_callback: An optional callback for streaming updates.
        :param temp_dir: The temporary directory to be cleaned up after the run.
        """
        logger.info(f"[{run_id}] Starting VeriFlow workflow...")

        initial_state: AgentState = {
            "run_id": run_id,
            "pdf_path": str(pdf_path),
            "repo_path": str(repo_path),
            "isa_json": None,
            "repo_context": None,
            "generated_code": {},
            "validation_errors": [],
            "retry_count": 0,
            "review_decision": None,
            "review_feedback": None
        }

        final_state = {}
        try:
            async for event in app_graph.astream(initial_state):
                if not stream_callback:
                    continue

                node_name = list(event.keys())[0]
                node_state = event[node_name]
                
                if "scholar" in event and event["scholar"].get("isa_json"):
                    isa_json_result = event["scholar"]["isa_json"]
                    confidence_scores = event["scholar"].get("confidence_scores", {})
                    
                    await stream_callback({
                        "type": "scholar_result",
                        "data": {
                            "run_id": run_id,
                            "hierarchy": {"investigation": isa_json_result},
                            "confidence_scores": confidence_scores
                        }
                    }, run_id)
                
                await stream_callback({
                    "type": "node_update",
                    "data": { "node": node_name, "state_keys": list(node_state.keys()) }
                }, run_id)
            
            final_state = event

            logger.info(f"[{run_id}] Workflow finished.")
            if stream_callback:
                await stream_callback({"type": "workflow_complete", "data": final_state}, run_id)

        except Exception as e:
            logger.error(f"[{run_id}] Workflow execution failed: {e}", exc_info=True)
            if stream_callback:
                await stream_callback({"type": "error", "data": str(e)}, run_id)
        
        # finally:
        #     # Cleanup the temporary directory
        #     if temp_dir and temp_dir.exists():
        #         try:
        #             shutil.rmtree(temp_dir)
        #             logger.info(f"[{run_id}] Successfully cleaned up directory: {temp_dir}")
        #         except Exception as e:
        #             logger.error(f"[{run_id}] Error cleaning up directory {temp_dir}: {e}")

veriflow_service = VeriFlowService()
