"""
VeriFlow - DAG Generator Service
Generates Airflow DAG Python files from CWL workflows.
Per SPEC.md Section 7.2
"""

import os
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
from datetime import datetime
import textwrap

from app.models.cwl import (
    ParsedWorkflow,
    CWLWorkflow,
    CWLStep,
    CWLCommandLineTool,
    DockerRequirement,
)
from app.services.cwl_parser import cwl_parser

logger = logging.getLogger(__name__)


class DAGGenerator:
    """
    Generates Airflow DAG Python files from parsed CWL workflows.
    
    Converts:
    - CWL Workflow → Airflow DAG
    - CWL CommandLineTool → DockerOperator or BashOperator
    - CWL step dependencies → Airflow task dependencies
    """
    
    # Default directory for generated DAGs
    DEFAULT_DAGS_PATH = os.getenv("AIRFLOW_DAGS_PATH", "/opt/airflow/dags")
    # Local dags path for development
    LOCAL_DAGS_PATH = Path(__file__).parent.parent.parent.parent / "airflow" / "dags"
    
    # MinIO configuration for volume mounts
    MINIO_DATA_PATH = os.getenv("MINIO_DATA_PATH", "/data/minio")
    
    def __init__(self, dags_path: Optional[Path] = None):
        """
        Initialize DAG generator.
        
        Args:
            dags_path: Directory to write generated DAG files
        """
        self.dags_path = dags_path or self.LOCAL_DAGS_PATH
        self.dags_path = Path(self.dags_path)
        self.dags_path.mkdir(parents=True, exist_ok=True)
    
    def generate_dag(
        self,
        workflow: ParsedWorkflow,
        execution_id: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate an Airflow DAG file from a parsed CWL workflow.
        
        Args:
            workflow: Parsed CWL workflow
            execution_id: Unique execution identifier
            config: Optional execution configuration
            
        Returns:
            Path to the generated DAG file
        """
        config = config or {}
        dag_id = self._generate_dag_id(workflow, execution_id)
        
        # Generate DAG Python code
        dag_code = self._generate_dag_code(
            workflow=workflow,
            dag_id=dag_id,
            execution_id=execution_id,
            config=config,
        )
        
        # Write to file
        dag_file = self.dags_path / f"{dag_id}.py"
        dag_file.write_text(dag_code)
        
        logger.info(f"Generated DAG file: {dag_file}")
        return str(dag_file)
    
    def _generate_dag_id(self, workflow: ParsedWorkflow, execution_id: str) -> str:
        """Generate unique DAG ID."""
        workflow_id = workflow.workflow.id or "workflow"
        # Clean up workflow_id for use in DAG ID
        clean_id = "".join(c if c.isalnum() else "_" for c in workflow_id)
        return f"veriflow_{clean_id}_{execution_id}"
    
    def _generate_dag_code(
        self,
        workflow: ParsedWorkflow,
        dag_id: str,
        execution_id: str,
        config: Dict[str, Any],
    ) -> str:
        """Generate the Python code for an Airflow DAG."""
        
        # Extract workflow info
        cwl_workflow = workflow.workflow
        steps = cwl_workflow.steps
        step_order = workflow.step_order
        dependencies = workflow.step_dependencies
        
        # Build imports
        imports = self._generate_imports(workflow)
        
        # Build DAG context
        dag_context = self._generate_dag_context(dag_id, cwl_workflow, execution_id, config)
        
        # Build tasks
        tasks = self._generate_tasks(workflow, execution_id, config)
        
        # Build dependencies
        task_deps = self._generate_dependencies(dependencies)
        
        # Combine all parts
        code = f'''"""
VeriFlow Generated DAG
Workflow: {cwl_workflow.label or cwl_workflow.id or 'Unknown'}
Execution ID: {execution_id}
Generated: {datetime.utcnow().isoformat()}

DO NOT EDIT - This file is auto-generated from CWL workflow.
"""

{imports}

# Execution configuration
EXECUTION_ID = "{execution_id}"
CONFIG = {repr(config)}

{dag_context}
{tasks}
{task_deps}
'''
        return code
    
    def _generate_imports(self, workflow: ParsedWorkflow) -> str:
        """Generate import statements."""
        imports = [
            "from datetime import datetime, timedelta",
            "import os",
            "",
            "from airflow import DAG",
            "from airflow.operators.bash import BashOperator",
            "from airflow.operators.python import PythonOperator",
            "from airflow.operators.empty import EmptyOperator",
        ]
        
        # Check if we need DockerOperator
        has_docker = any(
            self._get_docker_image(workflow, step_id)
            for step_id in workflow.workflow.steps
        )
        
        if has_docker:
            imports.append("from airflow.providers.docker.operators.docker import DockerOperator")
            imports.append("from docker.types import Mount")
        
        return "\n".join(imports)
    
    def _generate_dag_context(
        self,
        dag_id: str,
        cwl_workflow: CWLWorkflow,
        execution_id: str,
        config: Dict[str, Any],
    ) -> str:
        """Generate DAG definition context."""
        
        description = cwl_workflow.doc or cwl_workflow.label or f"VeriFlow workflow {execution_id}"
        
        return f'''
# Default arguments for tasks
default_args = {{
    'owner': 'veriflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}}

# DAG definition
with DAG(
    dag_id="{dag_id}",
    default_args=default_args,
    description="""{description}""",
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=["veriflow", "generated"],
    max_active_runs=1,
) as dag:
'''
    
    def _generate_tasks(
        self,
        workflow: ParsedWorkflow,
        execution_id: str,
        config: Dict[str, Any],
    ) -> str:
        """Generate task definitions for all workflow steps."""
        tasks = []
        
        # Start task
        tasks.append('''
    # Start marker task
    start = EmptyOperator(task_id="start")
''')
        
        # Generate task for each step
        for step_id in workflow.step_order:
            step = workflow.workflow.steps.get(step_id)
            if not step:
                continue
            
            task_code = self._generate_task(workflow, step_id, step, execution_id, config)
            tasks.append(task_code)
        
        # End task
        tasks.append('''
    # End marker task
    end = EmptyOperator(task_id="end")
''')
        
        return "\n".join(tasks)
    
    def _generate_task(
        self,
        workflow: ParsedWorkflow,
        step_id: str,
        step: CWLStep,
        execution_id: str,
        config: Dict[str, Any],
    ) -> str:
        """Generate a single task definition."""
        
        # Clean task ID for Airflow (alphanumeric and underscore only)
        task_id = "".join(c if c.isalnum() else "_" for c in step_id)
        
        # Check for Docker image
        docker_image = self._get_docker_image(workflow, step_id)
        
        if docker_image:
            return self._generate_docker_task(
                task_id, step, docker_image, execution_id, config
            )
        else:
            return self._generate_bash_task(
                task_id, step, execution_id, config
            )
    
    def _generate_docker_task(
        self,
        task_id: str,
        step: CWLStep,
        docker_image: str,
        execution_id: str,
        config: Dict[str, Any],
    ) -> str:
        """Generate a DockerOperator task."""
        
        # Build environment variables
        env_vars = {
            "EXECUTION_ID": execution_id,
            "STEP_ID": task_id,
            "INPUT_PATH": f"/data/input/{execution_id}",
            "OUTPUT_PATH": f"/data/output/{execution_id}/{task_id}",
        }
        
        # Add config as env vars
        for key, value in config.items():
            env_vars[f"CONFIG_{key.upper()}"] = str(value)
        
        return f'''
    # Task: {task_id}
    {task_id} = DockerOperator(
        task_id="{task_id}",
        image="{docker_image}",
        command="python -c \\"print('Executing {task_id}')\\"",
        environment={repr(env_vars)},
        mounts=[
            Mount(
                source="{self.MINIO_DATA_PATH}",
                target="/data",
                type="bind",
            ),
        ],
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
    )
'''
    
    def _generate_bash_task(
        self,
        task_id: str,
        step: CWLStep,
        execution_id: str,
        config: Dict[str, Any],
    ) -> str:
        """Generate a BashOperator task (fallback when no Docker image)."""
        
        # For MVP, create a simple echo command
        # In production, this would run the actual tool
        
        return f'''
    # Task: {task_id} (BashOperator fallback)
    {task_id} = BashOperator(
        task_id="{task_id}",
        bash_command="""
            echo "Executing step: {task_id}"
            echo "Execution ID: {execution_id}"
            echo "Step run: {step.run}"
            # Create output directory
            mkdir -p /tmp/veriflow/{execution_id}/{task_id}
            echo "Step completed at $(date)" > /tmp/veriflow/{execution_id}/{task_id}/status.txt
        """,
        env={{
            "EXECUTION_ID": "{execution_id}",
            "STEP_ID": "{task_id}",
        }},
    )
'''
    
    def _generate_dependencies(self, dependencies: Dict[str, List[str]]) -> str:
        """Generate task dependency statements."""
        lines = ["\n    # Task dependencies"]
        
        # All steps depend on start
        all_steps = set(dependencies.keys())
        for deps in dependencies.values():
            all_steps.update(deps)
        
        # Clean step IDs
        clean_steps = {s: "".join(c if c.isalnum() else "_" for c in s) for s in all_steps}
        
        # Steps with no dependencies depend on start
        root_steps = [s for s in all_steps if s not in dependencies or not dependencies[s]]
        for step in root_steps:
            clean_id = clean_steps[step]
            lines.append(f"    start >> {clean_id}")
        
        # Add explicit dependencies
        for step_id, deps in dependencies.items():
            clean_step = clean_steps[step_id]
            for dep in deps:
                clean_dep = clean_steps[dep]
                lines.append(f"    {clean_dep} >> {clean_step}")
        
        # End task depends on all leaf nodes (steps that nothing depends on)
        dependent_steps = set()
        for deps in dependencies.values():
            dependent_steps.update(deps)
        leaf_steps = [s for s in all_steps if s not in dependent_steps]
        
        if leaf_steps:
            for step in leaf_steps:
                clean_id = clean_steps[step]
                lines.append(f"    {clean_id} >> end")
        else:
            # If no leaves found, just connect end to all steps
            for step in all_steps:
                clean_id = clean_steps[step]
                lines.append(f"    {clean_id} >> end")
        
        return "\n".join(lines)
    
    def _get_docker_image(self, workflow: ParsedWorkflow, step_id: str) -> Optional[str]:
        """Get Docker image for a step from tool definition."""
        tool = workflow.tools.get(step_id)
        if not tool:
            return None
        
        docker_req = cwl_parser.get_docker_requirement(tool)
        if docker_req:
            return docker_req.docker_pull or docker_req.docker_image_id
        
        return None
    
    def delete_dag(self, dag_id: str) -> bool:
        """Delete a generated DAG file."""
        dag_file = self.dags_path / f"{dag_id}.py"
        if dag_file.exists():
            dag_file.unlink()
            logger.info(f"Deleted DAG file: {dag_file}")
            return True
        return False
    
    def list_generated_dags(self) -> List[str]:
        """List all generated VeriFlow DAG files."""
        dags = []
        for file in self.dags_path.glob("veriflow_*.py"):
            dags.append(file.stem)
        return dags


# Singleton instance
dag_generator = DAGGenerator()
