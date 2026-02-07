"""
VeriFlow Template DAG
This file serves as a template for dynamically generated VeriFlow workflow DAGs.
Actual DAGs will be generated in Stage 5 during CWL→Airflow conversion.
"""

from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator

# Template DAG for testing Airflow connectivity
with DAG(
    dag_id="veriflow_template",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["veriflow", "template"],
    description="VeriFlow template DAG for testing",
) as dag:
    
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")
    
    start >> end
