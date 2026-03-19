import io
import json
import os
from datetime import datetime

from minio import Minio


def _get_minio_client():
    """Crée un client MinIO depuis les variables d'environnement."""
    return Minio(
        os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False,
    )


def _write_silver(minio_client, doc_name, full_text, page_count):
    """Construit le JSON silver et l'écrit dans MinIO. Retourne la silver_key."""
    silver_data = {
        "source_file": f"bronze/{doc_name}",
        "extracted_text": full_text,
        "pages": page_count,
        "ocr_engine": "azure-document-intelligence",
        "processed_at": datetime.utcnow().isoformat() + "Z",
    }
    silver_key = "silver_" + doc_name.rsplit(".", 1)[0] + ".json"
    json_bytes = json.dumps(silver_data, ensure_ascii=False).encode("utf-8")
    minio_client.put_object(
        "silver",
        silver_key,
        io.BytesIO(json_bytes),
        len(json_bytes),
        content_type="application/json",
    )
    print(f"[SILVER] OCR → silver/{silver_key} ({len(full_text)} chars)")
    return silver_key


def store_silver(**context):
    """Tâche Airflow : écrit le JSON silver dans MinIO et passe les entités à gold."""
    ocr_output = context["ti"].xcom_pull(task_ids="azure_ocr")
    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")

    minio_client = _get_minio_client()
    _write_silver(
        minio_client,
        doc_name,
        ocr_output["full_text"],
        ocr_output["page_count"],
    )

    return ocr_output["entities"]
