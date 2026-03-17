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
    silver_key = "silver_" + doc_name.rsplit(".", 1)[0] + ".json"
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
    date_document = dates[0] if dates else None

    nlp = spacy.load("fr_core_news_md")
    doc = nlp(text[:100000])
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    raison_sociale = orgs[0] if orgs else None

    entities = {
        "montant_ht": montant_ht,
        "tva": tva,
        "montant_ttc": montant_ttc,
        "siret": siret,
        "date_document": date_document,
        "raison_sociale": raison_sociale,
        "doc_type": doc_type,
        "all_dates": dates,
        "all_orgs": orgs,
    }
    print(f"[NER] Entités extraites : {entities}")
    return entities
