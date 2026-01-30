"""
VeriFlow - Airflow Client Service
REST API client for Apache Airflow integration.
Per SPEC.md Section 7.3 and 7.4
"""

import os
import asyncio
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class DAGRunState(str, Enum):
    """Airflow DAG run states."""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class TaskInstanceState(str, Enum):
    """Airflow task instance states."""
    NONE = "none"
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    UP_FOR_RETRY = "up_for_retry"
    UP_FOR_RESCHEDULE = "up_for_reschedule"
    UPSTREAM_FAILED = "upstream_failed"
    SKIPPED = "skipped"
    REMOVED = "removed"


class AirflowClient:
    """
    Client for Apache Airflow REST API.
    
    Provides methods to:
    - Trigger DAG runs
    - Poll execution status
    - Retrieve task logs
    
    Uses session-based authentication per docker-compose configuration.
    """
    
    DEFAULT_BASE_URL = os.getenv("AIRFLOW_API_URL", "http://localhost:8080")
    DEFAULT_USERNAME = os.getenv("AIRFLOW_USERNAME", "airflow")
    DEFAULT_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "airflow")
    POLL_INTERVAL = 5  # seconds
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize Airflow client.
        
        Args:
            base_url: Airflow webserver URL
            username: Authentication username
            password: Authentication password
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.username = username or self.DEFAULT_USERNAME
        self.password = password or self.DEFAULT_PASSWORD
        self.api_base = f"{self.base_url}/api/v1"
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authentication."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.api_base,
                auth=(self.username, self.password),
                timeout=30.0,
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def health_check(self) -> bool:
        """Check if Airflow is healthy and accessible."""
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Airflow health check failed: {e}")
            return False
    
    async def get_dags(self) -> List[Dict[str, Any]]:
        """List all available DAGs."""
        try:
            client = await self._get_client()
            response = await client.get("/dags")
            response.raise_for_status()
            data = response.json()
            return data.get("dags", [])
        except Exception as e:
            logger.error(f"Failed to get DAGs: {e}")
            return []
    
    async def get_dag(self, dag_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific DAG."""
        try:
            client = await self._get_client()
            response = await client.get(f"/dags/{dag_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get DAG {dag_id}: {e}")
            return None
    
    async def trigger_dag(
        self,
        dag_id: str,
        conf: Optional[Dict[str, Any]] = None,
        logical_date: Optional[str] = None,
    ) -> Optional[str]:
        """
        Trigger a DAG run.
        
        Args:
            dag_id: ID of the DAG to trigger
            conf: Configuration to pass to the DAG
            logical_date: Optional execution date (ISO format)
            
        Returns:
            dag_run_id if successful, None otherwise
        """
        try:
            client = await self._get_client()
            
            payload: Dict[str, Any] = {}
            if conf:
                payload["conf"] = conf
            if logical_date:
                payload["logical_date"] = logical_date
            
            response = await client.post(
                f"/dags/{dag_id}/dagRuns",
                json=payload,
            )
            
            if response.status_code == 404:
                logger.error(f"DAG {dag_id} not found")
                return None
            
            response.raise_for_status()
            data = response.json()
            dag_run_id = data.get("dag_run_id")
            
            logger.info(f"Triggered DAG {dag_id}, run_id: {dag_run_id}")
            return dag_run_id
            
        except Exception as e:
            logger.error(f"Failed to trigger DAG {dag_id}: {e}")
            return None
    
    async def get_dag_run(self, dag_id: str, dag_run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a DAG run.
        
        Args:
            dag_id: DAG identifier
            dag_run_id: DAG run identifier
            
        Returns:
            DAG run details including state and task statuses
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/dags/{dag_id}/dagRuns/{dag_run_id}")
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get DAG run {dag_id}/{dag_run_id}: {e}")
            return None
    
    async def get_task_instances(
        self,
        dag_id: str,
        dag_run_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all task instances for a DAG run.
        
        Args:
            dag_id: DAG identifier
            dag_run_id: DAG run identifier
            
        Returns:
            List of task instance details
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances"
            )
            
            if response.status_code == 404:
                return []
            
            response.raise_for_status()
            data = response.json()
            return data.get("task_instances", [])
            
        except Exception as e:
            logger.error(f"Failed to get task instances: {e}")
            return []
    
    async def get_task_logs(
        self,
        dag_id: str,
        dag_run_id: str,
        task_id: str,
        task_try_number: int = 1,
    ) -> Optional[str]:
        """
        Get logs for a specific task instance.
        
        Args:
            dag_id: DAG identifier
            dag_run_id: DAG run identifier
            task_id: Task identifier
            task_try_number: Attempt number (default 1)
            
        Returns:
            Task logs as string
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{task_try_number}",
                headers={"Accept": "text/plain"},
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to get task logs: {e}")
            return None
    
    async def wait_for_dag_run(
        self,
        dag_id: str,
        dag_run_id: str,
        poll_interval: int = None,
        timeout: int = 3600,
        callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Wait for a DAG run to complete.
        
        Args:
            dag_id: DAG identifier
            dag_run_id: DAG run identifier
            poll_interval: Seconds between status checks
            timeout: Maximum wait time in seconds
            callback: Optional callback for status updates
            
        Returns:
            Final DAG run status
        """
        interval = poll_interval or self.POLL_INTERVAL
        start_time = datetime.utcnow()
        
        while True:
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                raise TimeoutError(f"DAG run {dag_run_id} timed out after {timeout}s")
            
            # Get current status
            dag_run = await self.get_dag_run(dag_id, dag_run_id)
            if not dag_run:
                raise ValueError(f"DAG run {dag_run_id} not found")
            
            state = dag_run.get("state", "")
            
            # Call callback if provided
            if callback:
                task_instances = await self.get_task_instances(dag_id, dag_run_id)
                await callback(dag_run, task_instances)
            
            # Check terminal states
            if state in [DAGRunState.SUCCESS.value, DAGRunState.FAILED.value]:
                return dag_run
            
            await asyncio.sleep(interval)
    
    def calculate_progress(self, task_instances: List[Dict[str, Any]]) -> int:
        """
        Calculate overall progress from task instances.
        
        Returns:
            Progress percentage (0-100)
        """
        if not task_instances:
            return 0
        
        completed = sum(
            1 for t in task_instances
            if t.get("state") in [TaskInstanceState.SUCCESS.value, TaskInstanceState.SKIPPED.value]
        )
        
        return int((completed / len(task_instances)) * 100)
    
    def map_task_state(self, airflow_state: str) -> str:
        """
        Map Airflow task state to VeriFlow node status.
        
        Args:
            airflow_state: Airflow task instance state
            
        Returns:
            VeriFlow node status (pending, running, completed, error)
        """
        state_mapping = {
            TaskInstanceState.NONE.value: "pending",
            TaskInstanceState.SCHEDULED.value: "pending",
            TaskInstanceState.QUEUED.value: "pending",
            TaskInstanceState.RUNNING.value: "running",
            TaskInstanceState.SUCCESS.value: "completed",
            TaskInstanceState.FAILED.value: "error",
            TaskInstanceState.UP_FOR_RETRY.value: "running",
            TaskInstanceState.UP_FOR_RESCHEDULE.value: "pending",
            TaskInstanceState.UPSTREAM_FAILED.value: "error",
            TaskInstanceState.SKIPPED.value: "completed",
            TaskInstanceState.REMOVED.value: "error",
        }
        return state_mapping.get(airflow_state, "pending")


# Singleton instance
airflow_client = AirflowClient()
