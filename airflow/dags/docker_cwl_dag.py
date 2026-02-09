"""
Docker CWL Test DAG
This DAG executes a CWL workflow that runs a Docker container step.
Uses cwltool with Docker-in-Docker to run containerized CWL tools.
Last touched: 2026-02-07 23:55
"""

from datetime import datetime
from pathlib import Path
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


# Default arguments for the DAG
default_args = {
    "retries": 0,
}

# Paths configuration
# Note: ./examples is mounted to /opt/airflow/cwl in docker-compose.yml
CWL_EXAMPLES_DIR = Path("/opt/airflow/cwl/cwl")
WORKFLOW_FILE = CWL_EXAMPLES_DIR / "docker_workflow.cwl"
JOB_FILE = CWL_EXAMPLES_DIR / "docker_job.yml"
OUTPUT_DIR = Path("/opt/airflow/cwl-output/docker_cwl")


def validate_cwl_files(**context):
    """Validate that CWL files exist and are readable."""
    import os
    
    errors = []
    
    if not WORKFLOW_FILE.exists():
        errors.append(f"Workflow file not found: {WORKFLOW_FILE}")
    if not JOB_FILE.exists():
        errors.append(f"Job file not found: {JOB_FILE}")
    
    if errors:
        raise FileNotFoundError("\n".join(errors))
    
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    return {
        "workflow": str(WORKFLOW_FILE),
        "job": str(JOB_FILE),
        "output_dir": str(OUTPUT_DIR)
    }


with DAG(
    dag_id="docker_cwl_test",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["veriflow", "cwl", "docker"],
    description="Run CWL workflow with Docker container step",
    default_args=default_args,
) as dag:
    
    # Task 1: Validate CWL files exist
    validate_files = PythonOperator(
        task_id="validate_cwl_files",
        python_callable=validate_cwl_files,
    )
    
    # Task 2: Run the CWL workflow using cwltool
    # cwltool will handle pulling and running the Docker image
    run_cwl = BashOperator(
        task_id="run_cwl_workflow",
        bash_command=f"""
            cd {OUTPUT_DIR} && \
            cwltool \
                --outdir {OUTPUT_DIR} \
                --timestamps \
                --verbose \
                {WORKFLOW_FILE} \
                {JOB_FILE}
        """,
    )
    
    # Task 3: Display the output
    show_output = BashOperator(
        task_id="show_output",
        bash_command=f"""
            echo "=== CWL Workflow Output ===" && \
            if [ -f {OUTPUT_DIR}/docker_output.txt ]; then
                cat {OUTPUT_DIR}/docker_output.txt
            else
                echo "Output file not found"
            fi
        """,
    )
    
    # Define task dependencies
    validate_files >> run_cwl >> show_output
