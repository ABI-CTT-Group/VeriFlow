FROM apache/airflow:3.0.6

# Install FAB provider for user management
RUN pip install --no-cache-dir apache-airflow-providers-fab apache-airflow-providers-docker

COPY dags /opt/airflow/dags
