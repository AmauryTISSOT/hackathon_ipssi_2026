from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from tasks.bronze import store_bronze
from tasks.azure_ocr import analyze_document
from tasks.silver import store_silver
from tasks.gold import validate_and_store_gold
from tasks.controls import perform_controls
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
    t_analyze = PythonOperator(task_id="azure_ocr", python_callable=analyze_document)
    t_silver = PythonOperator(task_id="store_silver", python_callable=store_silver)
    t_gold = PythonOperator(task_id="validate_and_store_gold", python_callable=validate_and_store_gold)
    t_controls = PythonOperator(task_id="perform_controls", python_callable=perform_controls)
    t_mongo = PythonOperator(task_id="save_to_mongodb", python_callable=save_to_mongodb)

    t_bronze >> t_analyze >> t_silver >> t_gold >> t_controls >> t_mongo
