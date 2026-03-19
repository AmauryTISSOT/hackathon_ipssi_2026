import os
import re

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
            "valable jusqu'au",
            "accepter ce devis",
            "devis n°",
            "devis nº",
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
    {
        "type": "rib",
        "keywords": [
            "relevé d'identité bancaire",
            "identité bancaire",
            "iban",
            "bic",
            "code banque",
            "code guichet",
            "clé rib",
        ],
    },
]

# Correspondance entre le taux de TVA (%) et l'enum Mongoose du backend
TAUX_TVA_VERS_ENUM = {
    2.1: "FR_21",
    5.5: "FR_55",
    10.0: "FR_100",
    20.0: "FR_200",
    1.05: "FR_1_05",
    1.75: "FR_1_75",
    8.5: "FR_85",
}


def _parse_french_number(s):
    """Convertit un nombre au format français (1 500,00) en float."""
    s = s.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    return float(s)


def _map_vat_rate(percent):
    """Mappe un pourcentage de TVA vers l'enum Mongoose."""
    if percent is None:
        return "FR_200"
    rounded = round(percent, 2)
    return TAUX_TVA_VERS_ENUM.get(rounded, "FR_200")


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


def _extract_invoice_lines(fields, taux_tva):
    """Extrait les lignes de facture depuis les champs Azure Items."""
    lines = []
    if "Items" not in fields or fields["Items"].value_array is None:
        return lines
    for item in fields["Items"].value_array:
        obj = item.value_object or {}
        label = obj.get("Description")
        label = label.value_string if label else None
        quantity = obj.get("Quantity")
        quantity = quantity.value_number if quantity else None
        unit_price = obj.get("UnitPrice")
        unit_price = unit_price.value_number if unit_price else None
        item_tax = obj.get("Tax")
        if (
            item_tax
            and item_tax.value_number is not None
            and unit_price
            and quantity
            and quantity > 0
        ):
            item_rate = (item_tax.value_number / (unit_price * quantity)) * 100
        else:
            item_rate = taux_tva
        lines.append(
            {
                "label": label,
                "quantity": quantity,
                "unit_price": unit_price,
                "vat_rate": _map_vat_rate(item_rate),
            }
        )
    return lines


def _extract_issuer(fields, full_text):
    """Extrait les infos émetteur pour les devis."""
    name = None
    if "VendorName" in fields and fields["VendorName"].value_string:
        name = fields["VendorName"].value_string
    address = None
    if "VendorAddress" in fields and fields["VendorAddress"].value_string:
        address = fields["VendorAddress"].value_string
    phone = None
    m = re.search(
        r"(?:Tél|Tel|Téléphone|Phone)\s*[.:]\s*([\d\s.+()-]+)", full_text, re.IGNORECASE
    )
    if m:
        phone = m.group(1).strip()
    email = None
    m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", full_text)
    if m:
        email = m.group(0)
    website = None
    m = re.search(r"(?:https?://)?(?:www\.)\S+", full_text, re.IGNORECASE)
    if m:
        website = m.group(0)
    return {
        "name": name,
        "address": address,
        "phone_number": phone,
        "email": email,
        "website": website,
    }


def _extract_kbis_entities(
    full_text, raison_sociale, forme_juridique, capital_social, code_naf, adresse_siege
):
    """Structure les entités K-bis en objets imbriqués conformes au modèle Mongoose."""
    registration_rcs = None
    m = re.search(r"RCS\s+(\w+\s+\d[\d\s]+)", full_text)
    if m:
        registration_rcs = m.group(1).strip()

    date_registration = None
    m = re.search(r"immatricul.*?(\d{2}/\d{2}/\d{4})", full_text, re.IGNORECASE)
    if m:
        date_registration = m.group(1)

    share_capital = 0.0
    if capital_social:
        m_cap = re.search(r"([\d\s]+(?:[.,]\d+)?)", capital_social)
        if m_cap:
            try:
                share_capital = _parse_french_number(m_cap.group(1))
            except ValueError:
                share_capital = 0.0

    duration = None
    m = re.search(r"Durée.*?(\d+)\s*ans", full_text, re.IGNORECASE)
    if m:
        duration = m.group(1)

    closing_date = None
    m = re.search(r"Clôture.*?exercice.*?(.+)", full_text, re.IGNORECASE)
    if m:
        closing_date = m.group(1).strip()

    legal_entity = {
        "registration_rcs": registration_rcs or "N/A",
        "date_registration": date_registration or "01/01/1970",
        "corporate_name": raison_sociale or "N/A",
        "legal_form": forme_juridique or "N/A",
        "share_capital": share_capital,
        "registered_address": adresse_siege or "N/A",
        "main_activities": code_naf or "N/A",
        "duration_legal_entity": duration or "01/01/2070",
        "financial_year_closing_date": closing_date or "N/A",
    }

    management = []
    for pattern in [
        r"(?:Gérant|Président|Directeur\s*général|Administrateur)\s*[:\s]*([A-ZÀ-Ü][a-zà-ü]+)\s+([A-ZÀ-Ü][a-zà-ü]+)",
        r"(Gérant|Président|Directeur|Administrateur)\s*[:\s]*M(?:me|r)?\.?\s*([A-ZÀ-Ü\s]+)",
    ]:
        for match in re.finditer(pattern, full_text):
            groups = match.groups()
            if len(groups) >= 2:
                management.append(
                    {
                        "category": "manager",
                        "first_name": groups[0].strip(),
                        "last_name": groups[1].strip(),
                        "birthdate": "1970-01-01",
                        "place_of_birth": "N/A",
                        "nationality": "Française",
                        "private_address": "N/A",
                    }
                )
        if management:
            break

    main_establishment = {
        "establishment_address": adresse_siege or "N/A",
        "trading_name": raison_sociale or "N/A",
        "activity": code_naf or "N/A",
        "commencement_activity": date_registration or "01/01/1970",
        "origin_business": "N/A",
        "method_operation": "N/A",
    }

    other_establishment = {
        "establishment_address": "N/A",
        "activity": "N/A",
        "commencement_activity": "01/01/1970",
        "origin_business": "N/A",
        "method_operation": "N/A",
    }

    return {
        "legal_entity": legal_entity,
        "management": management,
        "information_relating_activity_main_establishment": main_establishment,
        "information_relating_another_establishment_jurisdiction": other_establishment,
    }


def _extract_urssaf_entities(full_text, siret):
    """Extrait les entités spécifiques à l'attestation URSSAF, conformes au modèle Mongoose."""
    security_code = None
    m = re.search(
        r"code\s*(?:de\s*)?s[ée]curit[ée]\s*:?\s*([\w-]+)", full_text, re.IGNORECASE
    )
    if m:
        security_code = m.group(1)

    social_security = None
    m = re.search(r"[Nn][°ºo]\s*[Ss]écurité\s*[Ss]ociale\s*:?\s*(\d[\d\s]+)", full_text)
    if m:
        social_security = int(re.sub(r"\s", "", m.group(1)))

    internal_identifier = None
    m = re.search(r"[Ii]dentifiant\s*(?:interne)?\s*:?\s*([\w-]+)", full_text)
    if m:
        val = m.group(1)
        digits = re.sub(r"\D", "", val)
        internal_identifier = int(digits) if digits else None

    place_at = None
    m = re.search(r"[Ff]ait\s+[àa]\s*:?\s*(.+)", full_text)
    if m:
        place_at = m.group(1).strip().split("\n")[0].strip()

    created_at = None
    # Format ISO (2006-12-29)
    m = re.search(r"[Ll]e\s*:?\s*(\d{4}-\d{2}-\d{2})", full_text)
    if m:
        created_at = m.group(1)
    else:
        # Format français (29/12/2006)
        m = re.search(
            r"(?:Fait le|Date de délivrance|Le)\s*:?\s*(\d{2}/\d{2}/\d{4})",
            full_text,
            re.IGNORECASE,
        )
        if m:
            created_at = m.group(1)

    siren_int = None
    siret_int = None
    if siret and len(siret) == 14:
        siren_int = int(siret[:9])
        siret_int = int(siret)

    return {
        "siren": siren_int,
        "siret": siret_int,
        "social_security": social_security,
        "internal_identifier": internal_identifier,
        "security_code": security_code,
        "created_at": created_at,
        "place_at": place_at,
    }


def _extract_rib_entities(full_text):
    """Extrait les entités RIB par regex."""
    iban = None
    m = re.search(r"IBAN\s*[:\s]*([A-Z]{2}\d[\d\s]+)", full_text, re.IGNORECASE)
    if m:
        iban = re.sub(r"\s", "", m.group(1))

    bic = None
    m = re.search(
        r"BIC\s*[:\s]*([A-Z]{4}[A-Z]{2}[A-Z\d]{2,5})", full_text, re.IGNORECASE
    )
    if m:
        bic = m.group(1).strip()

    bank_code = None
    m = re.search(r"Code\s*Banque\s*[:\s]*(\d+)", full_text, re.IGNORECASE)
    if m:
        bank_code = m.group(1).strip()

    agency_code = None
    m = re.search(r"Code\s*Guichet\s*[:\s]*(\d+)", full_text, re.IGNORECASE)
    if m:
        agency_code = m.group(1).strip()

    account_number = None
    m = re.search(r"Num[ée]ro\s*de\s*compte\s*[:\s]*(\S+)", full_text, re.IGNORECASE)
    if m:
        account_number = m.group(1).strip()

    key = None
    m = re.search(r"Cl[ée]\s*(?:RIB)?\s*[:\s]*(\d+)", full_text, re.IGNORECASE)
    if m:
        key = int(m.group(1))

    registered_address = None
    m = re.search(r"Adresse\s*[:\s]*(.+)", full_text, re.IGNORECASE)
    if m:
        registered_address = m.group(1).strip()

    return {
        "iban": iban,
        "bic": bic,
        "bank_code": bank_code,
        "agency_code": agency_code,
        "account_number": account_number,
        "key": key,
        "registered_address": registered_address,
    }


def _get_minio_client():
    """Crée un client MinIO depuis les variables d'environnement."""
    return Minio(
        os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False,
    )


def _get_azure_client():
    """Crée un client Azure Document Intelligence depuis les variables d'environnement."""
    return DocumentIntelligenceClient(
        endpoint=os.environ["AZURE_DI_ENDPOINT"],
        credential=AzureKeyCredential(os.environ["AZURE_DI_KEY"]),
    )


def _download_from_bronze(minio_client, doc_name):
    """Télécharge un fichier depuis le bucket bronze de MinIO."""
    response = minio_client.get_object("bronze", doc_name)
    file_bytes = response.read()
    response.close()
    response.release_conn()
    return file_bytes



def _extract_azure_fields(result):
    """Extrait les champs structurés depuis le résultat Azure Document Intelligence."""
    montant_ht = None
    montant_ttc = None
    tva = None
    raison_sociale = None
    date_document = None
    due_date = None
    vendor_address = None
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
        if "InvoiceDateDue" in fields and fields["InvoiceDateDue"].value_date:
            d = fields["InvoiceDateDue"].value_date
            due_date = d.strftime("%d/%m/%Y")
        if "VendorAddress" in fields and fields["VendorAddress"].value_string:
            vendor_address = fields["VendorAddress"].value_string

    return {
        "montant_ht": montant_ht,
        "montant_ttc": montant_ttc,
        "tva": tva,
        "raison_sociale": raison_sociale,
        "date_document": date_document,
        "due_date": due_date,
        "vendor_address": vendor_address,
        "is_invoice": is_invoice,
    }


def _extract_siret(full_text):
    """Extrait le SIRET par regex (label SIRET + fallback 14 chiffres)."""
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
    return siret


def _extract_kbis_fields(full_text):
    """Extrait les champs spécifiques K-bis par regex."""
    raison_sociale = None
    m = re.search(r"Dénomination.*?\n(.+)", full_text)
    if m:
        raison_sociale = m.group(1).strip()

    siren = None
    m = re.search(r"SIREN\s*[:\s]*(\d[\d\s]{7,10}\d)", full_text)
    if m:
        siren = re.sub(r"\s", "", m.group(1))

    m = re.search(r"Forme juridique\s*\n(.+)", full_text)
    forme_juridique = m.group(1).strip() if m else None

    m = re.search(r"Capital social\s*\n?(\d[\d\s]*(?:[.,]\d+)?\s*€)", full_text)
    capital_social = m.group(1).strip() if m else None

    m = re.search(r"NAF\s*/\s*APE\s*\n?(\d{2}\.\d{2}[A-Z])", full_text)
    code_naf = m.group(1).strip() if m else None

    m = re.search(r"Adresse du siège\s*\n(.+)", full_text)
    adresse_siege = m.group(1).strip() if m else None

    return {
        "raison_sociale": raison_sociale,
        "siren": siren,
        "forme_juridique": forme_juridique,
        "capital_social": capital_social,
        "code_naf": code_naf,
        "adresse_siege": adresse_siege,
    }


def _extract_amounts_fallback(full_text, montant_ht, tva, montant_ttc):
    """Fallback regex pour les montants manquants. Retourne (ht, tva, ttc)."""
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
                r"(?:TVA|montant\s*TVA|total\s*TVA)\s*(?:\([^)]*\))?\s*[:\s]*"
                + montant_pattern,
                full_text,
                re.IGNORECASE,
            )
            if m:
                tva = _parse_french_number(m.group(1))

    return montant_ht, tva, montant_ttc


def _build_entities(
    doc_type,
    common,
    montant_ht,
    tva,
    montant_ttc,
    date_document,
    due_date,
    vendor_address,
    taux_tva,
    invoice_lines,
    is_invoice,
    result,
    full_text,
    siret,
    kbis_fields,
):
    """Construit le dictionnaire d'entités selon le type de document."""
    if doc_type == "facture":
        return {
            **common,
            "currency": "EUR",
            "language": "fr",
            "invoice_lines": invoice_lines,
            "issue_date": date_document,
            "due_date": due_date,
            "total_before_tax": montant_ht,
            "total_tax": tva,
            "total": montant_ttc,
            "taux_tva": taux_tva,
            "vendor_address": vendor_address,
            # kept for gold validation
            "montant_ht": montant_ht,
            "tva": tva,
            "montant_ttc": montant_ttc,
        }

    elif doc_type == "devis":
        issuer = {}
        payment_terms = None
        devis_label = None
        if is_invoice and result.documents:
            fields = result.documents[0].fields or {}
            issuer = _extract_issuer(fields, full_text)
            m = re.search(
                r"(?:conditions?\s*de\s*paiement|modalit[ée]s?\s*de\s*(?:r[eè]glement|paiement))\s*[:\s]*(.+)",
                full_text,
                re.IGNORECASE,
            )
            payment_terms = m.group(1).strip().split("\n")[0].strip() if m else None
            m = re.search(
                r"(?:devis|proposition)\s*n[°ºo]?\s*[:\s]*(\S+)",
                full_text,
                re.IGNORECASE,
            )
            devis_label = m.group(1).strip() if m else None
        return {
            **common,
            "label": devis_label,
            "quotation_lines": invoice_lines,
            "total_before_tax": montant_ht,
            "total_tva": tva,
            "total": montant_ttc,
            "issuer": issuer,
            "payment_terms": payment_terms,
            "issue_date": date_document,
            "due_date": due_date,
            "taux_tva": taux_tva,
            "vendor_address": vendor_address,
            # kept for gold validation
            "montant_ht": montant_ht,
            "tva": tva,
            "montant_ttc": montant_ttc,
        }

    elif doc_type == "kbis":
        raison_sociale = kbis_fields["raison_sociale"] or common.get("raison_sociale")
        kbis_data = _extract_kbis_entities(
            full_text,
            raison_sociale,
            kbis_fields["forme_juridique"],
            kbis_fields["capital_social"],
            kbis_fields["code_naf"],
            kbis_fields["adresse_siege"],
        )
        return {
            **common,
            "siren": kbis_fields["siren"],
            "code_naf": kbis_fields["code_naf"],
            "adresse_siege": kbis_fields["adresse_siege"],
            "legal_entity": kbis_data["legal_entity"],
            "management": kbis_data["management"],
            "information_relating_activity_main_establishment": kbis_data[
                "information_relating_activity_main_establishment"
            ],
            "information_relating_another_establishment_jurisdiction": kbis_data[
                "information_relating_another_establishment_jurisdiction"
            ],
        }

    elif doc_type == "attestation_urssaf":
        urssaf_data = _extract_urssaf_entities(full_text, siret)
        return {
            **common,
            **urssaf_data,
        }

    elif doc_type == "rib":
        rib_data = _extract_rib_entities(full_text)
        return {
            **common,
            **rib_data,
        }

    else:
        return {
            **common,
            "montant_ht": montant_ht,
            "tva": tva,
            "montant_ttc": montant_ttc,
            "date_document": date_document,
            "vendor_address": vendor_address,
        }


def analyze_document(**context):
    """Tâche Airflow : OCR + extraction d'entités via Azure Document Intelligence."""
    # Connexion aux services
    minio_client = _get_minio_client()
    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")
    file_bytes = _download_from_bronze(minio_client, doc_name)

    di_client = _get_azure_client()
    poller = di_client.begin_analyze_document("prebuilt-invoice", body=file_bytes)
    result = poller.result()
    full_text = result.content or ""
    page_count = len(result.pages) if result.pages else 0

    # Extraction des champs Azure
    azure_fields = _extract_azure_fields(result)
    montant_ht = azure_fields["montant_ht"]
    tva = azure_fields["tva"]
    montant_ttc = azure_fields["montant_ttc"]
    raison_sociale = azure_fields["raison_sociale"]
    date_document = azure_fields["date_document"]
    due_date = azure_fields["due_date"]
    vendor_address = azure_fields["vendor_address"]
    is_invoice = azure_fields["is_invoice"]

    # Extraction SIRET et dates
    siret = _extract_siret(full_text)
    dates = re.findall(r"\b(\d{2}/\d{2}/\d{4})\b", full_text)
    if not date_document and dates:
        date_document = dates[0]

    # Classification
    doc_type = classify_by_keywords(full_text)
    if is_invoice and doc_type == "inconnu":
        doc_type = "facture"

    # Taux de TVA par regex
    taux_tva = None
    m = re.search(r"TVA\s*\(?\s*(\d+(?:[.,]\d+)?)\s*%", full_text, re.IGNORECASE)
    if m:
        taux_tva = float(m.group(1).replace(",", "."))

    # Lignes de facture/devis
    invoice_lines = []
    if is_invoice and result.documents:
        fields = result.documents[0].fields or {}
        invoice_lines = _extract_invoice_lines(fields, taux_tva)

    # Champs K-bis
    kbis_fields = _extract_kbis_fields(full_text) if doc_type == "kbis" else {}
    if doc_type == "kbis" and kbis_fields.get("raison_sociale"):
        raison_sociale = kbis_fields["raison_sociale"]

    # Fallback montants
    montant_ht, tva, montant_ttc = _extract_amounts_fallback(
        full_text, montant_ht, tva, montant_ttc
    )

    # Champs communs
    all_orgs = [raison_sociale] if raison_sociale else []
    common = {
        "doc_type": doc_type,
        "siret": siret,
        "raison_sociale": raison_sociale,
        "all_dates": dates,
        "all_orgs": all_orgs,
    }

    # Construction des entités
    entities = _build_entities(
        doc_type,
        common,
        montant_ht,
        tva,
        montant_ttc,
        date_document,
        due_date,
        vendor_address,
        taux_tva,
        invoice_lines,
        is_invoice,
        result,
        full_text,
        siret,
        kbis_fields,
    )

    print(f"[AZURE] Entités extraites : {entities}")
    return {
        "entities": entities,
        "full_text": full_text,
        "page_count": page_count,
    }
