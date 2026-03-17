import io
import json
import os
import re
from datetime import datetime

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from minio import Minio

# Règles de classification par mots-clés (fallback si Azure ne détecte pas le type)
CLASSIFICATION_RULES = [
    {
        "type": "facture",
        "keywords": [
            "facture",
            "invoice",
            "montant ht",
            "montant ttc",
            "total ht",
            "total ttc",
            "net à payer",
            "échéance",
        ],
    },
    {
        "type": "devis",
        "keywords": [
            "devis",
            "proposition commerciale",
            "offre de prix",
            "validité de l'offre",
            "bon pour accord",
            "référence devis",
        ],
    },
    {
        "type": "kbis",
        "keywords": [
            "kbis",
            "extrait kbis",
            "registre du commerce",
            "greffe du tribunal",
            "immatriculation",
            "rcs",
        ],
    },
    {
        "type": "attestation_urssaf",
        "keywords": [
            "attestation de vigilance",
            "urssaf",
            "cotisations sociales",
            "obligations sociales",
            "sécurité sociale",
            "attestation de fourniture",
        ],
    },
]


def _parse_french_number(s):
    """Convertit un nombre au format français (1 500,00) en float."""
    s = s.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    return float(s)


def classify_by_keywords(text):
    """Classification par comptage de mots-clés."""
    text_lower = text.lower()
    scores = {}
    for rule in CLASSIFICATION_RULES:
        score = sum(1 for kw in rule["keywords"] if kw in text_lower)
        if score > 0:
            scores[rule["type"]] = score
    if scores:
        return max(scores, key=scores.get)
    return "inconnu"


def analyze_document(**context):
    """Tâche Airflow : OCR + extraction d'entités via Azure Document Intelligence."""
    # Connexion MinIO
    client = Minio(
        os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False,
    )

    # Téléchargement du document depuis le bucket bronze
    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")
    response = client.get_object("bronze", doc_name)
    file_bytes = response.read()
    response.close()
    response.release_conn()

    # Client Azure Document Intelligence
    di_client = DocumentIntelligenceClient(
        endpoint=os.environ["AZURE_DI_ENDPOINT"],
        credential=AzureKeyCredential(os.environ["AZURE_DI_KEY"]),
    )

    # Analyse avec le modèle prebuilt-invoice (factures/devis)
    poller = di_client.begin_analyze_document(
        "prebuilt-invoice",
        body=file_bytes,
    )
    result = poller.result()

    # Récupération du texte OCR complet
    full_text = result.content or ""

    # Écriture du JSON silver dans MinIO (même structure qu'avant)
    silver_data = {
        "source_file": f"bronze/{doc_name}",
        "extracted_text": full_text,
        "pages": len(result.pages) if result.pages else 0,
        "ocr_engine": "azure-document-intelligence",
        "processed_at": datetime.utcnow().isoformat() + "Z",
    }
    silver_key = "silver_" + doc_name.rsplit(".", 1)[0] + ".json"
    json_bytes = json.dumps(silver_data, ensure_ascii=False).encode("utf-8")
    client.put_object(
        "silver",
        silver_key,
        io.BytesIO(json_bytes),
        len(json_bytes),
        content_type="application/json",
    )
    print(f"[AZURE] OCR → silver/{silver_key} ({len(full_text)} chars)")

    # Extraction des entités depuis les champs Azure (facture détectée)
    montant_ht = None
    montant_ttc = None
    tva = None
    raison_sociale = None
    date_document = None
    is_invoice = False

    if result.documents:
        doc = result.documents[0]
        fields = doc.fields or {}
        is_invoice = True

        if "SubTotal" in fields and fields["SubTotal"].value_number is not None:
            montant_ht = fields["SubTotal"].value_number
        if "TotalTax" in fields and fields["TotalTax"].value_number is not None:
            tva = fields["TotalTax"].value_number
        if "InvoiceTotal" in fields and fields["InvoiceTotal"].value_number is not None:
            montant_ttc = fields["InvoiceTotal"].value_number
        if "VendorName" in fields and fields["VendorName"].value_string:
            raison_sociale = fields["VendorName"].value_string
        if "InvoiceDate" in fields and fields["InvoiceDate"].value_date:
            d = fields["InvoiceDate"].value_date
            date_document = d.strftime("%d/%m/%Y")

    # Extraction SIRET par regex
    siret = None
    m = re.search(r"SIRET\s*[:\s]*(\d[\d\s]{12,16}\d)", full_text, re.IGNORECASE)
    if m:
        siret = re.sub(r"\s", "", m.group(1))
        if len(siret) != 14:
            siret = None
    if siret is None:
        m = re.search(r"\b(\d{14})\b", full_text)
        if m:
            siret = m.group(1)

    # Extraction des dates par regex
    dates = re.findall(r"\b(\d{2}/\d{2}/\d{4})\b", full_text)
    if not date_document and dates:
        date_document = dates[0]

    # Classification du document
    if is_invoice:
        # Si Azure détecte une facture, on distingue facture/devis par mots-clés
        kw_type = classify_by_keywords(full_text)
        doc_type = "devis" if kw_type == "devis" else "facture"
    else:
        # Sinon, classification complète par mots-clés (kbis, attestation_urssaf, etc.)
        doc_type = classify_by_keywords(full_text)

    # Fallback regex pour les montants si Azure ne les a pas trouvés
    if montant_ht is None or montant_ttc is None or tva is None:
        montant_pattern = r"(\d[\d\s\u00a0]*(?:[.,]\d{1,2})?)"

        if montant_ht is None:
            m = re.search(
                r"(?:montant\s*HT|total\s*HT|HT)\s*[:\s]*" + montant_pattern,
                full_text,
                re.IGNORECASE,
            )
            if m:
                montant_ht = _parse_french_number(m.group(1))

        if montant_ttc is None:
            m = re.search(
                r"(?:montant\s*TTC|total\s*TTC|TTC|net\s*[àa]\s*payer)\s*[:\s]*"
                + montant_pattern,
                full_text,
                re.IGNORECASE,
            )
            if m:
                montant_ttc = _parse_french_number(m.group(1))

        if tva is None:
            m = re.search(
                r"(?:TVA|montant\s*TVA|total\s*TVA)\s*[:\s]*" + montant_pattern,
                full_text,
                re.IGNORECASE,
            )
            if m:
                tva = _parse_french_number(m.group(1))

    # Liste des organisations (depuis Azure ou raison_sociale)
    all_orgs = [raison_sociale] if raison_sociale else []

    entities = {
        "montant_ht": montant_ht,
        "tva": tva,
        "montant_ttc": montant_ttc,
        "siret": siret,
        "date_document": date_document,
        "raison_sociale": raison_sociale,
        "doc_type": doc_type,
        "all_dates": dates,
        "all_orgs": all_orgs,
    }
    print(f"[AZURE] Entités extraites : {entities}")
    return entities
