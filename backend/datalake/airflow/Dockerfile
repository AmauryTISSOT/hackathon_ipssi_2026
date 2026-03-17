FROM apache/airflow:3.1.8-python3.12

USER airflow
RUN pip install --no-cache-dir \
    azure-ai-documentintelligence \
    minio \
    pymongo \
    apache-airflow-providers-fab
