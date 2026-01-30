"""
VeriFlow - Execution Engine Service
Orchestrates workflow execution from CWL to Airflow.
Coordinates CWL parsing, DAG generation, and execution monitoring.
Per SPEC.md Section 7
"""

import os
import asyncio
import logging
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime
from pathlib import Path
import uuid
import json

from app.models.cwl import (
    ParsedWorkflow,
    CWLParseResult,
)
from app.models.execution import (
    ExecutionStatus,
    LogLevel,
    NodeExecutionStatus,
    LogEntry,
)
from app.services.cwl_parser import cwl_parser, CWLParser
from app.services.dag_generator import dag_generator, DAGGenerator
from app.services.airflow_client import airflow_client, AirflowClient
from app.services.docker_builder import docker_builder, DockerBuilder
from app.services.minio_client import minio_service

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Core execution engine for VeriFlow workflows.
    
    Orchestrates:
    1. CWL parsing and validation
    2. DAG generation
    3. Docker image preparation
    4. Airflow execution
    5. Status monitoring and WebSocket streaming
    6. Results storage and provenance tracking
    """
    
    def __init__(
        self,
        cwl_parser: CWLParser = None,
        dag_generator: DAGGenerator = None,
        airflow_client: AirflowClient = None,
        docker_builder: DockerBuilder = None,
    ):
        """Initialize execution engine with service dependencies."""
        self.cwl_parser = cwl_parser or cwl_parser
        self.dag_generator = dag_generator or dag_generator
        self.airflow_client = airflow_client or airflow_client
        self.docker_builder = docker_builder or docker_builder
        
        # Active executions for status tracking
        self.active_executions: Dict[str, Dict[str, Any]] = {}
    
    async def prepare_execution(
        self,
        cwl_content: str,
        workflow_id: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare a workflow for execution.
        
        Args:
            cwl_content: CWL YAML content
            workflow_id: Workflow identifier
            config: Execution configuration
            
        Returns:
            Preparation result with execution_id and status
        """
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        config = config or {}
        
        try:
            # Parse CWL workflow
            logger.info(f"Parsing CWL workflow for execution {execution_id}")
            parse_result = self.cwl_parser.parse_workflow(cwl_content)
            
            if not parse_result.success:
                return {
                    "success": False,
                    "execution_id": execution_id,
                    "error": f"CWL parsing failed: {parse_result.error}",
                    "validation": parse_result.validation,
                }
            
            workflow = parse_result.workflow
            
            # Validate workflow
            if parse_result.validation and not parse_result.validation.valid:
                return {
                    "success": False,
                    "execution_id": execution_id,
                    "error": "CWL validation failed",
                    "validation": parse_result.validation,
                }
            
            # Generate DAG
            logger.info(f"Generating Airflow DAG for execution {execution_id}")
            dag_path = self.dag_generator.generate_dag(
                workflow=workflow,
                execution_id=execution_id,
                config=config,
            )
            
            # Generate DAG ID
            dag_id = self.dag_generator._generate_dag_id(workflow, execution_id)
            
            # Generate Dockerfiles for tools (MVP: placeholder images)
            tool_images = {}
            for step_id, tool in workflow.tools.items():
                dockerfile = self.docker_builder.generate_dockerfile(
                    tool=tool,
                    tool_id=step_id,
                )
                image_name = self.docker_builder.get_image_name(
                    tool=tool,
                    tool_id=step_id,
                    use_placeholder=True,  # MVP uses placeholders
                )
                tool_images[step_id] = image_name
            
            # Store execution metadata
            self.active_executions[execution_id] = {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "dag_id": dag_id,
                "dag_path": dag_path,
                "status": ExecutionStatus.QUEUED,
                "workflow": workflow,
                "config": config,
                "tool_images": tool_images,
                "step_order": workflow.step_order,
                "created_at": datetime.utcnow().isoformat(),
                "logs": [],
                "node_statuses": {},
            }
            
            return {
                "success": True,
                "execution_id": execution_id,
                "dag_id": dag_id,
                "dag_path": dag_path,
                "steps": workflow.step_order,
                "tool_images": tool_images,
            }
            
        except Exception as e:
            logger.error(f"Execution preparation failed: {e}")
            return {
                "success": False,
                "execution_id": execution_id,
                "error": str(e),
            }
    
    async def start_execution(
        self,
        execution_id: str,
        status_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Start workflow execution via Airflow.
        
        Args:
            execution_id: Prepared execution ID
            status_callback: Optional callback for status updates
            
        Returns:
            Execution start result
        """
        if execution_id not in self.active_executions:
            return {
                "success": False,
                "error": f"Execution {execution_id} not found",
            }
        
        exec_data = self.active_executions[execution_id]
        dag_id = exec_data["dag_id"]
        
        try:
            # Check Airflow health
            is_healthy = await self.airflow_client.health_check()
            if not is_healthy:
                logger.warning("Airflow not healthy, proceeding with simulation mode")
                return await self._simulate_execution(execution_id, status_callback)
            
            # Wait for DAG to be picked up by Airflow
            await asyncio.sleep(2)
            
            # Check if DAG exists
            dag = await self.airflow_client.get_dag(dag_id)
            if not dag:
                logger.warning(f"DAG {dag_id} not found in Airflow, using simulation mode")
                return await self._simulate_execution(execution_id, status_callback)
            
            # Trigger DAG run
            logger.info(f"Triggering DAG {dag_id}")
            dag_run_id = await self.airflow_client.trigger_dag(
                dag_id=dag_id,
                conf=exec_data["config"],
            )
            
            if not dag_run_id:
                return {
                    "success": False,
                    "error": "Failed to trigger DAG",
                }
            
            # Update execution state
            exec_data["dag_run_id"] = dag_run_id
            exec_data["status"] = ExecutionStatus.RUNNING
            exec_data["started_at"] = datetime.utcnow().isoformat()
            
            # Add log entry
            self._add_log(
                execution_id,
                LogLevel.INFO,
                f"DAG {dag_id} triggered, run_id: {dag_run_id}",
            )
            
            # Start background monitoring if callback provided
            if status_callback:
                asyncio.create_task(
                    self._monitor_execution(execution_id, status_callback)
                )
            
            return {
                "success": True,
                "execution_id": execution_id,
                "dag_id": dag_id,
                "dag_run_id": dag_run_id,
                "status": ExecutionStatus.RUNNING,
            }
            
        except Exception as e:
            logger.error(f"Failed to start execution: {e}")
            exec_data["status"] = ExecutionStatus.FAILED
            self._add_log(execution_id, LogLevel.ERROR, str(e))
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _simulate_execution(
        self,
        execution_id: str,
        status_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Simulate execution when Airflow is not available.
        Used for MVP demo and testing.
        """
        exec_data = self.active_executions[execution_id]
        
        exec_data["status"] = ExecutionStatus.RUNNING
        exec_data["started_at"] = datetime.utcnow().isoformat()
        exec_data["simulation"] = True
        
        self._add_log(
            execution_id,
            LogLevel.WARNING,
            "Running in simulation mode (Airflow not available)",
        )
        
        # Start background simulation
        asyncio.create_task(
            self._run_simulation(execution_id, status_callback)
        )
        
        return {
            "success": True,
            "execution_id": execution_id,
            "dag_id": exec_data["dag_id"],
            "status": ExecutionStatus.RUNNING,
            "simulation": True,
        }
    
    async def _run_simulation(
        self,
        execution_id: str,
        status_callback: Optional[Callable] = None,
    ):
        """Run a simulated execution for demo purposes."""
        exec_data = self.active_executions.get(execution_id)
        if not exec_data:
            return
        
        step_order = exec_data.get("step_order", [])
        
        # Simulate each step
        for i, step_id in enumerate(step_order):
            # Update status to running
            exec_data["node_statuses"][step_id] = {
                "status": "running",
                "progress": 0,
                "started_at": datetime.utcnow().isoformat(),
            }
            
            self._add_log(
                execution_id,
                LogLevel.INFO,
                f"Starting step: {step_id}",
                node_id=step_id,
            )
            
            if status_callback:
                await status_callback(exec_data)
            
            # Simulate processing time
            for progress in range(0, 101, 25):
                await asyncio.sleep(0.5)
                exec_data["node_statuses"][step_id]["progress"] = progress
                if status_callback:
                    await status_callback(exec_data)
            
            # Mark step complete
            exec_data["node_statuses"][step_id] = {
                "status": "completed",
                "progress": 100,
                "completed_at": datetime.utcnow().isoformat(),
            }
            
            self._add_log(
                execution_id,
                LogLevel.INFO,
                f"Completed step: {step_id}",
                node_id=step_id,
            )
            
            # Update overall progress
            exec_data["overall_progress"] = int(((i + 1) / len(step_order)) * 100)
            
            if status_callback:
                await status_callback(exec_data)
        
        # Mark execution complete
        exec_data["status"] = ExecutionStatus.COMPLETED
        exec_data["completed_at"] = datetime.utcnow().isoformat()
        
        self._add_log(
            execution_id,
            LogLevel.INFO,
            "Workflow execution completed successfully",
        )
        
        # Generate mock results
        await self._generate_mock_results(execution_id)
        
        if status_callback:
            await status_callback(exec_data)
    
    async def _monitor_execution(
        self,
        execution_id: str,
        status_callback: Callable,
    ):
        """Monitor execution status via Airflow API."""
        exec_data = self.active_executions.get(execution_id)
        if not exec_data:
            return
        
        dag_id = exec_data["dag_id"]
        dag_run_id = exec_data.get("dag_run_id")
        
        if not dag_run_id:
            return
        
        try:
            while True:
                # Get DAG run status
                dag_run = await self.airflow_client.get_dag_run(dag_id, dag_run_id)
                if not dag_run:
                    break
                
                state = dag_run.get("state", "")
                
                # Get task instances
                task_instances = await self.airflow_client.get_task_instances(
                    dag_id, dag_run_id
                )
                
                # Update node statuses
                for task in task_instances:
                    task_id = task.get("task_id")
                    task_state = task.get("state", "")
                    
                    exec_data["node_statuses"][task_id] = {
                        "status": self.airflow_client.map_task_state(task_state),
                        "airflow_state": task_state,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                
                # Calculate overall progress
                exec_data["overall_progress"] = self.airflow_client.calculate_progress(
                    task_instances
                )
                
                # Check terminal states
                if state == "success":
                    exec_data["status"] = ExecutionStatus.COMPLETED
                    self._add_log(execution_id, LogLevel.INFO, "Execution completed")
                    await self._collect_results(execution_id)
                    await status_callback(exec_data)
                    break
                elif state == "failed":
                    exec_data["status"] = ExecutionStatus.FAILED
                    self._add_log(execution_id, LogLevel.ERROR, "Execution failed")
                    await status_callback(exec_data)
                    break
                
                await status_callback(exec_data)
                await asyncio.sleep(5)  # Poll interval
                
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            exec_data["status"] = ExecutionStatus.FAILED
            self._add_log(execution_id, LogLevel.ERROR, f"Monitoring error: {e}")
    
    async def _collect_results(self, execution_id: str):
        """Collect results from completed execution."""
        exec_data = self.active_executions.get(execution_id)
        if not exec_data:
            return
        
        # In production, would collect outputs from MinIO
        # For MVP, generate mock results
        await self._generate_mock_results(execution_id)
    
    async def _generate_mock_results(self, execution_id: str):
        """Generate mock results for demo purposes."""
        exec_data = self.active_executions.get(execution_id)
        if not exec_data:
            return
        
        # Create mock result files
        results = [
            {
                "path": f"derivative/sub-001/tumor_mask.nii.gz",
                "node_id": "segmentation",
                "size": 1048576,
                "mime_type": "application/x-nifti",
            },
            {
                "path": f"derivative/sub-001/segmentation_overlay.png",
                "node_id": "segmentation",
                "size": 524288,
                "mime_type": "image/png",
            },
        ]
        
        exec_data["results"] = results
        
        # Generate provenance
        provenance = self._generate_provenance(execution_id)
        exec_data["provenance"] = provenance
    
    def _generate_provenance(self, execution_id: str) -> Dict[str, Any]:
        """Generate provenance metadata (wasDerivedFrom relationships)."""
        exec_data = self.active_executions.get(execution_id)
        if not exec_data:
            return {}
        
        workflow_id = exec_data.get("workflow_id", "unknown")
        
        return {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "generated_at": datetime.utcnow().isoformat(),
            "entities": {
                "input": {
                    "type": "measurements",
                    "path": "measurements/mama-mia/primary/",
                },
                "output": {
                    "type": "process",
                    "path": f"process/{execution_id}/derivative/",
                    "wasDerivedFrom": "input",
                },
            },
            "activities": [
                {
                    "step_id": step_id,
                    "used": ["input"],
                    "generated": ["output"],
                }
                for step_id in exec_data.get("step_order", [])
            ],
        }
    
    def _add_log(
        self,
        execution_id: str,
        level: LogLevel,
        message: str,
        node_id: Optional[str] = None,
    ):
        """Add a log entry to execution."""
        exec_data = self.active_executions.get(execution_id)
        if not exec_data:
            return
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.value if isinstance(level, LogLevel) else level,
            "message": message,
            "node_id": node_id,
        }
        
        exec_data["logs"].append(log_entry)
        logger.log(
            getattr(logging, level.value if isinstance(level, LogLevel) else level, "INFO"),
            f"[{execution_id}] {message}"
        )
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an execution."""
        return self.active_executions.get(execution_id)
    
    def get_execution_logs(
        self,
        execution_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get recent logs for an execution."""
        exec_data = self.active_executions.get(execution_id)
        if not exec_data:
            return []
        return exec_data.get("logs", [])[-limit:]
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        exec_data = self.active_executions.get(execution_id)
        if not exec_data:
            return False
        
        # Mark as cancelled
        exec_data["status"] = ExecutionStatus.FAILED
        exec_data["cancelled_at"] = datetime.utcnow().isoformat()
        self._add_log(execution_id, LogLevel.WARNING, "Execution cancelled by user")
        
        return True


# Singleton instance
execution_engine = ExecutionEngine(
    cwl_parser=cwl_parser,
    dag_generator=dag_generator,
    airflow_client=airflow_client,
    docker_builder=docker_builder,
)
