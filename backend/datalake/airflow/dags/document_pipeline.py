from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from tasks.bronze import store_bronze
from tasks.azure_analyze import analyze_document
from tasks.gold import validate_and_store_gold
from tasks.mongodb import save_to_mongodb


with DAG(
    dag_id="document_pipeline",
    description="Pipeline de traitement de documents administratifs",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["hackathon", "documents"],
) as dag:

    t_bronze = PythonOperator(task_id="store_bronze", python_callable=store_bronze)
    t_analyze = PythonOperator(task_id="analyze_document", python_callable=analyze_document)
    t_gold = PythonOperator(task_id="validate_and_store_gold", python_callable=validate_and_store_gold)
    t_mongo = PythonOperator(task_id="save_to_mongodb", python_callable=save_to_mongodb)

    t_bronze >> t_analyze >> t_gold >> t_mongo
