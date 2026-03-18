import os
from datetime import datetime

from pymongo import MongoClient


def _parse_date(date_str):
    """Convertit une date dd/mm/yyyy ou yyyy-mm-dd en datetime, retourne None si invalide."""
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


# Alias conservé pour rétrocompatibilité des tests
_parse_iso_date = _parse_date


def _upsert_and_get_id(collection, filter_dict, record):
    """Upsert un document et retourne son _id."""
    result = collection.update_one(filter_dict, {"$set": record}, upsert=True)
    return result.upserted_id or collection.find_one(filter_dict)["_id"]


def _ensure_date(value, default):
    """Convertit une string en datetime avec fallback, retourne default si impossible."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return _parse_date(value) or default
    return default


def _save_facture(db, entities, company_id):
    record = {
        "currency": entities.get("currency", "EUR"),
        "language": entities.get("language", "fr"),
        "invoice_lines": entities.get("invoice_lines", []),
        "issue_date": _parse_date(entities.get("issue_date")),
        "due_date": _parse_date(entities.get("due_date")),
        "total_before_tax": entities.get("total_before_tax"),
        "total_tax": entities.get("total_tax"),
        "total": entities.get("total"),
    }
    if company_id:
        record["company_id"] = company_id
    db.invoices.update_one(
        {
            "company_id": company_id,
            "issue_date": record["issue_date"],
            "total": record["total"],
        },
        {"$set": record},
        upsert=True,
    )
    print("[MONGODB] Facture sauvegardée")


def _save_devis(db, entities, company_id):
    record = {
        "label": entities.get("label"),
        "quotation_lines": entities.get("quotation_lines", []),
        "total_before_tax": entities.get("total_before_tax"),
        "total_tva": entities.get("total_tva"),
        "total": entities.get("total"),
        "issuer": entities.get("issuer", {}),
        "payment_terms": entities.get("payment_terms"),
        "issue_date": _parse_date(entities.get("issue_date")),
        "due_date": _parse_date(entities.get("due_date")),
    }
    if company_id:
        record["company_id"] = company_id
    db.quotations.update_one(
        {
            "company_id": company_id,
            "issue_date": record["issue_date"],
            "total": record["total"],
        },
        {"$set": record},
        upsert=True,
    )
    print("[MONGODB] Devis sauvegardé")


def _save_kbis(db, entities, company_id):
    if not company_id:
        print("[MONGODB] KBIS: pas de company_id, skip (required field)")
        return False

    legal_entity = entities.get("legal_entity", {})
    legal_entity["date_registration"] = _ensure_date(
        legal_entity.get("date_registration"), datetime(1970, 1, 1)
    )
    legal_entity["duration_legal_entity"] = _ensure_date(
        legal_entity.get("duration_legal_entity"), datetime(2070, 1, 1)
    )

    management = entities.get("management", [])
    for mgr in management:
        if isinstance(mgr.get("birthdate"), str):
            mgr["birthdate"] = _ensure_date(mgr["birthdate"], datetime(1970, 1, 1))

    main_est = entities.get("information_relating_activity_main_establishment", {})
    if isinstance(main_est.get("commencement_activity"), str):
        main_est["commencement_activity"] = _ensure_date(
            main_est["commencement_activity"], datetime(1970, 1, 1)
        )

    other_est = entities.get(
        "information_relating_another_establishment_jurisdiction", {}
    )
    if isinstance(other_est.get("commencement_activity"), str):
        other_est["commencement_activity"] = _ensure_date(
            other_est["commencement_activity"], datetime(1970, 1, 1)
        )

    record = {
        "legal_entity": legal_entity,
        "management": management,
        "information_relating_activity_main_establishment": main_est,
        "information_relating_another_establishment_jurisdiction": other_est,
        "company_id": company_id,
    }
    db.kbis.update_one(
        {"company_id": company_id},
        {"$set": record},
        upsert=True,
    )
    print("[MONGODB] KBIS sauvegardé")
    return True


def _save_attestation_urssaf(db, entities, company_id):
    record = {
        "siren": entities.get("siren"),
        "siret": entities.get("siret"),
        "social_security": entities.get("social_security"),
        "internal_identifier": entities.get("internal_identifier"),
        "security_code": entities.get("security_code"),
        "created_at": _parse_date(entities.get("created_at")),
        "place_at": entities.get("place_at"),
    }
    if company_id:
        record["company_id"] = company_id
    db.certificateemergencyurssafs.update_one(
        {
            "siret": record.get("siret"),
            "security_code": record.get("security_code"),
        },
        {"$set": record},
        upsert=True,
    )
    print("[MONGODB] Attestation URSSAF sauvegardée")


def _save_rib(db, entities, company_id):
    record = {
        "iban": entities.get("iban"),
        "bic": entities.get("bic"),
        "bank_code": entities.get("bank_code"),
        "agency_code": entities.get("agency_code"),
        "account_number": entities.get("account_number"),
        "key": entities.get("key"),
        "registered_address": entities.get("registered_address"),
    }
    if company_id:
        record["company_id"] = company_id
    db.ribs.update_one(
        {"iban": record.get("iban")},
        {"$set": record},
        upsert=True,
    )
    print("[MONGODB] RIB sauvegardé")


_SAVE_DISPATCH = {
    "facture": _save_facture,
    "devis": _save_devis,
    "kbis": _save_kbis,
    "attestation_urssaf": _save_attestation_urssaf,
    "rib": _save_rib,
}


def save_to_mongodb(**context):

    gold_data = context["ti"].xcom_pull(task_ids="validate_and_store_gold")
    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")
    entities = gold_data["entities"]
    alerts = gold_data["validation"]["alerts"]
    doc_type = entities.get("doc_type")

    mongo_client = MongoClient(os.environ["MONGO_URI"])
    db = mongo_client["hackathon"]

    # 1. Document record
    doc_record = {
        "filename": doc_name,
        "doc_type": doc_type,
        "status": "processed",
        "bronze_path": f"bronze/{doc_name}",
        "silver_path": f"silver/silver_{doc_name.rsplit('.', 1)[0]}.json",
        "gold_path": f"gold/gold_{doc_name.rsplit('.', 1)[0]}.json",
        "processed_at": gold_data["processed_at"],
    }
    doc_id = _upsert_and_get_id(db.documents, {"filename": doc_name}, doc_record)

    # 2. Alerts
    if alerts:
        alert_docs = [
            {
                **alert,
                "document_id": doc_id,
                "filename": doc_name,
                "created_at": gold_data["processed_at"],
            }
            for alert in alerts
        ]
        db.alerts.insert_many(alert_docs)

    # 3. Company
    siret_raw = entities.get("siret")
    siret = str(siret_raw) if siret_raw is not None else None
    company_id = None
    if siret:
        siren_str = siret[:9]
        nic = siret[9:14]
        company_record = {
            "siret": siret,
            "siren": siren_str,
            "nic": nic,
            "denomination_unite_legale": entities.get("raison_sociale"),
            "country": "FR",
        }
        code_naf = entities.get("code_naf")
        if code_naf:
            company_record["activite_principale_unite_legale"] = code_naf

        address = entities.get("vendor_address") or entities.get("adresse_siege")
        if address:
            company_record["adresseEtablissement"] = address

        company_id = _upsert_and_get_id(db.companies, {"siret": siret}, company_record)

    # 4. Dispatch par type de document
    save_fn = _SAVE_DISPATCH.get(doc_type)
    if save_fn:
        result = save_fn(db, entities, company_id)
        if result is False:
            mongo_client.close()
            return
    else:
        print(f"[MONGODB] Type inconnu '{doc_type}', pas de collection typée")

    mongo_client.close()
    print(f"[MONGODB] Sauvegardé — doc_id={doc_id}, {len(alerts)} alerte(s)")
