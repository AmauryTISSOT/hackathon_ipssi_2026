import os
import random
from pathlib import Path
from datetime import datetime

import pandas as pd
from faker import Faker
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from data.utils import get_project_root, safe, convert

ROOT_DIR = get_project_root()
BASE_PATH = os.path.join(ROOT_DIR, "data", "data_sirene")
SILVER_PATH = os.path.join(BASE_PATH, "formatted_data")

execution_date = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = os.path.join(ROOT_DIR, "data", "fake_data", "rib", execution_date)
os.makedirs(OUTPUT_DIR, exist_ok=True)

fake = Faker("fr_FR")

BANKS = [
    {"name": "BNP Paribas", "code_banque": "30004", "bic": "BNPAFRPP", "logo": "bnp.png"},
    {"name": "Société Générale", "code_banque": "30003", "bic": "SOGEFRPP", "logo": "sg.png"},
    {"name": "Crédit Agricole", "code_banque": "30006", "bic": "AGRIFRPP", "logo": "ca.png"},
    {"name": "La Banque Postale", "code_banque": "20041", "bic": "PSSTFRPP", "logo": "lbp.png"},
]

def compute_rib_key(bank, branch, account):
    account_num = "".join(convert(c) for c in account)
    rib_number = f"{bank}{branch}{account_num}"
    key = 97 - (int(rib_number) % 97)
    return f"{key:02d}"


def compute_iban(bank, branch, account, rib_key):
    account_num = "".join(convert(c) for c in account)
    rib = f"{bank}{branch}{account_num}{rib_key}"
    temp = rib + "1527"
    iban_key = 98 - (int(temp) % 97)
    return f"FR{iban_key:02d}{rib}"


def get_rib_holder(company):
    denom = company.get("denominationUniteLegale")
    if denom and denom.strip():
        return denom.strip(), "entreprise"

    nom = company.get("nomUniteLegale")
    prenom = company.get("prenom1UniteLegale") or company.get("prenomUsuelUniteLegale")

    if nom and prenom:
        return f"{prenom.strip()} {nom.strip()}", "personne"
    if nom:
        return nom.strip(), "personne"
    return "Titulaire Inconnu", "inconnu"

def get_address(company):
    return company.get("adresseEtablissement") or (
        f"{company.get('numeroVoieEtablissement','')}"
        f"{company.get('typeVoieEtablissement','')}"
        f"{company.get('libelleVoieEtablissement','')}, "
        f"{company.get('codePostalEtablissement','')}"
        f"{company.get('libelleCommuneEtablissement','')}"
    )

def generate_rib(company):
    bank = random.choice(BANKS)
    code_banque = bank["code_banque"]
    code_guichet = str(random.randint(10000, 99999))
    account = "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=11))
    rib_key = compute_rib_key(code_banque, code_guichet, account)
    iban = compute_iban(code_banque, code_guichet, account, rib_key)
    holder, type_holder = get_rib_holder(company)
    return {
        "titulaire": holder,
        "type": type_holder,
        "adresse": get_address(company),
        "banque": bank["name"],
        "logo_banque": bank["logo"],
        "bic": bank["bic"],
        "code_banque": code_banque,
        "code_guichet": code_guichet,
        "numero_compte": account,
        "cle_rib": rib_key,
        "iban": iban,
        "agence": fake.city(),
    }


def rib_to_pdf(rib, filename):
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("<b>RELEVÉ D'IDENTITÉ BANCAIRE</b>", styles["Title"]),
        Spacer(1, 12),

        Paragraph(f"<b>Titulaire :</b> {rib['titulaire']}", styles["Normal"]),
        Paragraph(f"<b>Adresse :</b> {rib['adresse']}", styles["Normal"]),
        Spacer(1, 10),

        Paragraph(f"<b>Banque :</b> {rib['banque']}", styles["Normal"]),
        Paragraph(f"<b>Agence :</b> {rib['agence']}", styles["Normal"]),
        Paragraph(f"<b>BIC :</b> {rib['bic']}", styles["Normal"]),
        Spacer(1, 10),

        Paragraph(f"<b>Code Banque :</b> {rib['code_banque']}", styles["Normal"]),
        Paragraph(f"<b>Code Guichet :</b> {rib['code_guichet']}", styles["Normal"]),
        Paragraph(f"<b>Numéro de compte :</b> {rib['numero_compte']}", styles["Normal"]),
        Paragraph(f"<b>Clé RIB :</b> {rib['cle_rib']}", styles["Normal"]),
        Spacer(1, 10),

        Paragraph(f"<b>IBAN :</b> {rib['iban']}", styles["Normal"]),
    ]

    doc.build(elements)

def main():
    parquet_files = list(Path(SILVER_PATH).glob("*.parquet"))

    if not parquet_files:
        print(f"Erreur : Aucun fichier Parquet trouvé dans : {SILVER_PATH}")
        return

    input_file = max(parquet_files, key=lambda f: f.stat().st_mtime)
    print(f"Fichier sélectionné : {input_file.name}")

    try:
        df_silver = pd.read_parquet(input_file)
    except Exception as e:
        print(f"Erreur lors de la lecture du Parquet : {e}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    limit = min(10, len(df_silver))
    print(f"Génération de {limit} fichiers RIB...")

    for index, row in df_silver.head(limit).iterrows():
        company = row.to_dict()

        if isinstance(company.get("metadata"), dict):
            company.update(company["metadata"])

        siret = safe(company.get("siret", fake.numerify("#########")))
        rib = generate_rib(company)

        pdf_path = Path(OUTPUT_DIR) / f"rib_{siret}_{index:03d}.pdf"
        print(f"→ {pdf_path}")

        rib_to_pdf(rib, str(pdf_path))

if __name__ == "__main__":
    main()