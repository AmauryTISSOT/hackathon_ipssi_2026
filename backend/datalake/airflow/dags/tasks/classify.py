CLASSIFICATION_RULES = [
    {
        "type": "facture",
        "keywords": [
            "facture", "invoice", "montant ht", "montant ttc",
            "total ht", "total ttc", "net à payer", "échéance",
        ],
    },
    {
        "type": "devis",
        "keywords": [
            "devis", "proposition commerciale", "offre de prix",
            "validité de l'offre", "bon pour accord", "référence devis",
        ],
    },
    {
        "type": "kbis",
        "keywords": [
            "kbis", "extrait kbis", "registre du commerce",
            "greffe du tribunal", "immatriculation", "rcs",
        ],
    },
    {
        "type": "attestation_urssaf",
        "keywords": [
            "attestation de vigilance", "urssaf", "cotisations sociales",
            "obligations sociales", "sécurité sociale", "attestation de fourniture",
        ],
    },
]


def classify_document(**context):
    text = context["ti"].xcom_pull(task_ids="extract_ocr")
    text_lower = text.lower()

    scores = {}
    for rule in CLASSIFICATION_RULES:
        score = sum(1 for kw in rule["keywords"] if kw in text_lower)
        if score > 0:
            scores[rule["type"]] = score

    if scores:
        doc_type = max(scores, key=scores.get)
    else:
        doc_type = "inconnu"

    print(f"[CLASSIFY] Type détecté : {doc_type} (scores: {scores})")
    return doc_type
