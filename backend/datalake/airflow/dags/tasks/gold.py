import io
import json
import os
from datetime import datetime

from minio import Minio


def validate_and_store_gold(**context):

    entities = context["ti"].xcom_pull(task_ids="store_silver")
    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")
    alerts = []

    doc_type = entities.get("doc_type")

    # Validation montants uniquement pour factures et devis
    if doc_type in ("facture", "devis"):
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
    gold_key = "gold_" + doc_name.rsplit(".", 1)[0] + ".json"
    json_bytes = json.dumps(gold_data, ensure_ascii=False).encode("utf-8")
    client.put_object(
        "gold", gold_key, io.BytesIO(json_bytes), len(json_bytes),
        content_type="application/json",
    )

    print(f"[GOLD] Écrit dans gold/{gold_key} — {len(alerts)} alerte(s)")
    return gold_data
