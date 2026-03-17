import os

from pymongo import MongoClient


def save_to_mongodb(**context):

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
        "silver_path": f"silver/silver_{doc_name.rsplit('.', 1)[0]}.json",
        "gold_path": f"gold/gold_{doc_name.rsplit('.', 1)[0]}.json",
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
            "date_document": entities.get("date_document"),
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
