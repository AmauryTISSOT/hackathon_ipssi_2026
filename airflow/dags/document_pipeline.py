from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def store_bronze(**context):
    doc_name = context["dag_run"].conf.get("doc_name", "facture_example.pdf")
    print(f"[BRONZE] Document '{doc_name}' prêt dans le bucket bronze.")
    return doc_name


def classify_document(**context):
    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")
    doc_type = "facture"
    print(f"[CLASSIFY] Document '{doc_name}' classifié comme : {doc_type}")
    return doc_type


def extract_ocr(**context):
    from minio import Minio
    import easyocr
    from pdf2image import convert_from_bytes
    import json, os, io
    import numpy as np
    from PIL import Image

    client = Minio(
        os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False,
    )

    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")
    response = client.get_object("bronze", doc_name)
    file_bytes = response.read()
    response.close()
    response.release_conn()

    reader = easyocr.Reader(["fr"], gpu=True)

    if doc_name.lower().endswith(".pdf"):
        images = convert_from_bytes(file_bytes, dpi=150)
        all_results = []
        for page_num, image in enumerate(images):
            img_array = np.array(image)
            results = reader.readtext(img_array, batch_size=8)
            all_results.append({
                "page": page_num + 1,
                "blocks": [
                    {"text": text, "confidence": float(conf)}
                    for (bbox, text, conf) in results
                ],
            })
    else:
        image = Image.open(io.BytesIO(file_bytes))
        img_array = np.array(image)
        results = reader.readtext(img_array, batch_size=8)
        all_results = [{
            "page": 1,
            "blocks": [
                {"text": text, "confidence": float(conf)}
                for (bbox, text, conf) in results
            ],
        }]

    full_text = "\n".join(
        block["text"] for page in all_results for block in page["blocks"]
    )
    silver_data = {
        "source_file": f"bronze/{doc_name}",
        "extracted_text": full_text,
        "pages": len(all_results),
        "details": all_results,
        "ocr_engine": "easyocr",
        "processed_at": datetime.utcnow().isoformat() + "Z",
    }

    silver_key = doc_name.rsplit(".", 1)[0] + ".json"
    json_bytes = json.dumps(silver_data, ensure_ascii=False).encode("utf-8")
    client.put_object(
        "silver", silver_key, io.BytesIO(json_bytes), len(json_bytes),
        content_type="application/json",
    )

    print(f"[OCR] {len(all_results)} page(s), {len(full_text)} chars → silver/{silver_key}")
    return full_text


def store_silver(**context):
    doc_type = context["ti"].xcom_pull(task_ids="classify_document")
    text = context["ti"].xcom_pull(task_ids="extract_ocr")
    print(f"[SILVER] Confirmé dans silver — type={doc_type}, texte={len(text)} chars")


def extract_ner(**context):
    import re, json, os, io
    from minio import Minio
    import spacy

    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")
    doc_type = context["ti"].xcom_pull(task_ids="classify_document")

    client = Minio(
        os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False,
    )
    silver_key = doc_name.rsplit(".", 1)[0] + ".json"
    response = client.get_object("silver", silver_key)
    silver_data = json.loads(response.read().decode("utf-8"))
    response.close()
    response.release_conn()

    text = silver_data.get("extracted_text", "")

    def parse_french_number(s):
        s = s.replace("\u00a0", "").replace(" ", "").replace(",", ".")
        return float(s)

    montant_pattern = r"(\d[\d\s\u00a0]*(?:[.,]\d{1,2}))"

    montant_ht = None
    m = re.search(r"(?:montant\s*HT|total\s*HT|HT)\s*[:\s]*" + montant_pattern, text, re.IGNORECASE)
    if m:
        montant_ht = parse_french_number(m.group(1))

    montant_ttc = None
    m = re.search(r"(?:montant\s*TTC|total\s*TTC|TTC|net\s*[àa]\s*payer)\s*[:\s]*" + montant_pattern, text, re.IGNORECASE)
    if m:
        montant_ttc = parse_french_number(m.group(1))

    tva = None
    m = re.search(r"(?:TVA|montant\s*TVA|total\s*TVA)\s*[:\s]*" + montant_pattern, text, re.IGNORECASE)
    if m:
        tva = parse_french_number(m.group(1))

    siret = None
    m = re.search(r"\b(\d{14})\b", text)
    if m:
        siret = m.group(1)
    else:
        m = re.search(r"SIRET\s*[:\s]*(\d[\d\s]{12,16}\d)", text, re.IGNORECASE)
        if m:
            siret = re.sub(r"\s", "", m.group(1))
            if len(siret) != 14:
                siret = None

    dates = re.findall(r"\b(\d{2}/\d{2}/\d{4})\b", text)
    date_facture = dates[0] if dates else None

    nlp = spacy.load("fr_core_news_md")
    doc = nlp(text[:100000])
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    raison_sociale = orgs[0] if orgs else None

    entities = {
        "montant_ht": montant_ht,
        "tva": tva,
        "montant_ttc": montant_ttc,
        "siret": siret,
        "date_facture": date_facture,
        "raison_sociale": raison_sociale,
        "doc_type": doc_type,
        "all_dates": dates,
        "all_orgs": orgs,
    }
    print(f"[NER] Entités extraites : {entities}")
    return entities


def validate_and_store_gold(**context):
    import json, os, io
    from minio import Minio

    entities = context["ti"].xcom_pull(task_ids="extract_ner")
    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")
    alerts = []

    ht = entities.get("montant_ht")
    tva = entities.get("tva")
    ttc = entities.get("montant_ttc")
    if ht is not None and tva is not None and ttc is not None:
        if abs(ttc - (ht + tva)) > 0.01:
            alerts.append({
                "type": "tva_mismatch",
                "message": f"HT ({ht}) + TVA ({tva}) = {ht + tva} != TTC ({ttc})",
                "severity": "error",
            })
    elif ttc is None or ht is None:
        alerts.append({
            "type": "missing_amounts",
            "message": "Montant HT ou TTC non trouvé",
            "severity": "warning",
        })

    siret = entities.get("siret")
    siret_valid = False
    if siret and len(siret) == 14 and siret.isdigit():
        siren = siret[:9]
        total = 0
        for i, ch in enumerate(siren):
            d = int(ch)
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        siret_valid = total % 10 == 0
        if not siret_valid:
            alerts.append({
                "type": "siret_invalid",
                "message": f"SIRET {siret} : checksum Luhn invalide sur SIREN {siren}",
                "severity": "error",
            })
    elif siret:
        alerts.append({
            "type": "siret_format",
            "message": f"SIRET '{siret}' n'a pas 14 chiffres",
            "severity": "error",
        })

    for d in entities.get("all_dates", []):
        try:
            parsed = datetime.strptime(d, "%d/%m/%Y")
            if parsed > datetime(2030, 1, 1):
                alerts.append({
                    "type": "date_future",
                    "message": f"Date {d} semble trop lointaine",
                    "severity": "warning",
                })
        except ValueError:
            pass

    gold_data = {
        "source_file": f"bronze/{doc_name}",
        "entities": entities,
        "validation": {
            "alerts": alerts,
            "siret_valid": siret_valid,
            "tva_valid": len([a for a in alerts if a["type"] == "tva_mismatch"]) == 0,
        },
        "processed_at": datetime.utcnow().isoformat() + "Z",
    }

    client = Minio(
        os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False,
    )
    gold_key = doc_name.rsplit(".", 1)[0] + ".json"
    json_bytes = json.dumps(gold_data, ensure_ascii=False).encode("utf-8")
    client.put_object(
        "gold", gold_key, io.BytesIO(json_bytes), len(json_bytes),
        content_type="application/json",
    )

    print(f"[GOLD] Écrit dans gold/{gold_key} — {len(alerts)} alerte(s)")
    return gold_data


def save_to_mongodb(**context):
    import os
    from pymongo import MongoClient

    gold_data = context["ti"].xcom_pull(task_ids="validate_and_store_gold")
    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")
    entities = gold_data["entities"]
    alerts = gold_data["validation"]["alerts"]

    mongo_client = MongoClient(os.environ["MONGO_URI"])
    db = mongo_client["hackathon"]

    doc_record = {
        "filename": doc_name,
        "doc_type": entities.get("doc_type"),
        "status": "processed",
        "bronze_path": f"bronze/{doc_name}",
        "silver_path": f"silver/{doc_name.rsplit('.', 1)[0]}.json",
        "gold_path": f"gold/{doc_name.rsplit('.', 1)[0]}.json",
        "processed_at": gold_data["processed_at"],
    }
    result = db.documents.update_one(
        {"filename": doc_name}, {"$set": doc_record}, upsert=True
    )
    doc_id = result.upserted_id or db.documents.find_one({"filename": doc_name})["_id"]

    db.extracted_data.update_one(
        {"document_id": doc_id},
        {"$set": {
            "document_id": doc_id,
            "filename": doc_name,
            "montant_ht": entities.get("montant_ht"),
            "montant_ttc": entities.get("montant_ttc"),
            "tva": entities.get("tva"),
            "siret": entities.get("siret"),
            "date_facture": entities.get("date_facture"),
            "raison_sociale": entities.get("raison_sociale"),
            "all_dates": entities.get("all_dates", []),
            "all_orgs": entities.get("all_orgs", []),
        }},
        upsert=True,
    )

    if alerts:
        alert_docs = [
            {**alert, "document_id": doc_id, "filename": doc_name,
             "created_at": gold_data["processed_at"]}
            for alert in alerts
        ]
        db.alerts.insert_many(alert_docs)

    siret = entities.get("siret")
    if siret and gold_data["validation"]["siret_valid"]:
        db.suppliers.update_one(
            {"siret": siret},
            {"$set": {
                "siret": siret,
                "raison_sociale": entities.get("raison_sociale"),
            }, "$addToSet": {
                "documents": doc_id,
            }},
            upsert=True,
        )

    mongo_client.close()
    print(f"[MONGODB] Sauvegardé — doc_id={doc_id}, {len(alerts)} alerte(s)")


with DAG(
    dag_id="document_pipeline",
    description="Pipeline de traitement de documents administratifs",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["hackathon", "documents"],
) as dag:

    t_bronze = PythonOperator(task_id="store_bronze", python_callable=store_bronze)
    t_classify = PythonOperator(task_id="classify_document", python_callable=classify_document)
    t_ocr = PythonOperator(task_id="extract_ocr", python_callable=extract_ocr)
    t_silver = PythonOperator(task_id="store_silver", python_callable=store_silver)
    t_ner = PythonOperator(task_id="extract_ner", python_callable=extract_ner)
    t_gold = PythonOperator(task_id="validate_and_store_gold", python_callable=validate_and_store_gold)
    t_mongo = PythonOperator(task_id="save_to_mongodb", python_callable=save_to_mongodb)

    t_bronze >> [t_classify, t_ocr]
    [t_classify, t_ocr] >> t_silver
    t_silver >> t_ner
    t_ner >> t_gold
    t_gold >> t_mongo
