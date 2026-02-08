FROM apache/airflow:3.0.6

# Install FAB provider for user management, Docker provider, and CWL tools
RUN pip install --no-cache-dir \
    apache-airflow-providers-fab \
    apache-airflow-providers-docker \
    cwltool>=3.1.20231114134824 \
    pyyaml

COPY dags /opt/airflow/dags
