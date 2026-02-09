"""
VeriFlow Service
"""
import logging
import shutil
import json
import os
import inspect
from pathlib import Path
from typing import Optional, Callable, Any, Dict, Union

from app.graph.workflow import app_graph, create_workflow
from app.state import AgentState
from app.services.database_sqlite import database_service

logger = logging.getLogger(__name__)

class VeriFlowService:
    
    async def run_workflow(
        self,
        run_id: str,
        pdf_path: Union[str, Path],
        repo_path: Union[str, Path],
        stream_callback: Optional[Callable] = None,
        temp_dir: Optional[Path] = None,
        user_context: Optional[str] = None,
        client_id: Optional[str] = None
    ):
        """
        Run the VeriFlow langraph workflow from scratch.
        """
        logger.info(f"[{run_id}] Starting VeriFlow workflow...")
        
        # 1. PERSIST CONTEXT IMMEDIATELY
        database_service.create_or_update_agent_session(
            run_id=run_id,
            user_context=user_context
        )

        initial_state: AgentState = {
            "run_id": run_id,
            "pdf_path": str(pdf_path),
            "repo_path": str(repo_path),
            "user_context": user_context,
            "isa_json": None,
            "repo_context": None,
            "generated_code": {},
            "validation_errors": [],
            "retry_count": 0,
            "review_decision": None,
            "review_feedback": None,
            "agent_directives": {},
            "client_id": client_id
        }

        await self._execute_graph(app_graph, initial_state, stream_callback, run_id, temp_dir)


    async def restart_workflow(
        self,
        run_id: str,
        start_node: str,
        stream_callback: Optional[Callable] = None
    ):
        """
        Restart the workflow from a specific agent node.
        """
        logger.info(f"[{run_id}] Restarting workflow from node: {start_node}")
        
        # 1. Reconstruct State from DB/Disk
        recovered_state = database_service.get_full_state_mock(run_id)
        if not recovered_state:
            raise ValueError(f"Run ID {run_id} not found or state is missing.")
            
        # 2. Reset / Initialize Transient Fields
        recovered_state["validation_errors"] = []
        recovered_state["review_decision"] = None
        
        # FIX: Ensure retry_count exists
        if "retry_count" not in recovered_state:
            recovered_state["retry_count"] = 0
            
        # FIX: Ensure agent_directives exists
        if "agent_directives" not in recovered_state:
            recovered_state["agent_directives"] = {}
        
        # 3. Create Dynamic Graph Entry Point
        dynamic_graph = create_workflow(entry_point=start_node)
        
        # 4. Execute
        await self._execute_graph(dynamic_graph, recovered_state, stream_callback, run_id)


    async def _execute_graph(
        self, 
        graph, 
        initial_state: AgentState, 
        stream_callback, 
        run_id, 
        temp_dir=None
    ):
        """Internal helper to stream graph execution."""
        try:
            async for event in graph.astream(initial_state):
                if not stream_callback:
                    continue

                node_name = list(event.keys())[0]
                
                payload = None
                if "scholar" in event:
                    payload = {"type": "scholar_complete", "data": {"run_id": run_id}}
                elif "engineer" in event:
                    payload = {"type": "engineer_complete", "data": {"run_id": run_id}}
                elif "validate" in event:
                    payload = {"type": "validation_complete", "data": {"run_id": run_id}}
                else:
                    payload = {"type": "node_update", "data": {"node": node_name}}
                
                await self._safe_callback(stream_callback, payload, run_id)

            logger.info(f"[{run_id}] Workflow finished.")
            if stream_callback:
                await self._safe_callback(stream_callback, {"type": "workflow_complete", "data": {"run_id": run_id}}, run_id)

        except Exception as e:
            logger.error(f"[{run_id}] Workflow execution failed: {e}", exc_info=True)
            if stream_callback:
                await self._safe_callback(stream_callback, {"type": "error", "data": str(e)}, run_id)
        
        finally:
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass

    async def _safe_callback(self, callback: Callable, message: Dict, run_id: str):
        """
        Safely invokes the callback, handling cases where it accepts 1 or 2 arguments.
        """
        try:
            await callback(message, run_id)
        except TypeError as e:
            if "positional arguments" in str(e):
                await callback(message)
            else:
                raise e

veriflow_service = VeriFlowService()