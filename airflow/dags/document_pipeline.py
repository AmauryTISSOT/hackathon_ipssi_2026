from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from tasks.bronze import store_bronze
from tasks.ocr import extract_ocr
from tasks.classify import classify_document
from tasks.ner import extract_ner
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
    t_ocr = PythonOperator(task_id="extract_ocr", python_callable=extract_ocr)
    t_classify = PythonOperator(task_id="classify_document", python_callable=classify_document)
    t_ner = PythonOperator(task_id="extract_ner", python_callable=extract_ner)
    t_gold = PythonOperator(task_id="validate_and_store_gold", python_callable=validate_and_store_gold)
    t_mongo = PythonOperator(task_id="save_to_mongodb", python_callable=save_to_mongodb)

    t_bronze >> t_ocr >> t_classify >> t_ner >> t_gold >> t_mongo
