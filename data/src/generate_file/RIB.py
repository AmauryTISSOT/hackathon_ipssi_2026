import copy
import os
import random
import argparse
import json
from pathlib import Path
from datetime import datetime
from faker import Faker
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from dotenv import load_dotenv

from utils import get_project_root, safe, convert, get_mongodb_connection

ROOT_DIR = get_project_root()
load_dotenv(os.path.join(ROOT_DIR, ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "Hackathon")
COLLECTION_NAME = "Company"

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


def get_companies_from_mongodb(limit=None, sirets=None, filters=None, random_selection=False):
    client, collection = get_mongodb_connection(MONGODB_URI, DB_NAME, COLLECTION_NAME)
    companies = []
    try:
        query = {}
        if filters:
            query.update(filters)
        if sirets:
            query['siret'] = {'$in': sirets}
        print(f"Requête MongoDB: {query}")
        cursor = collection.find(query)
        if limit:
            cursor = cursor.limit(limit)
        companies = list(cursor)
        if random_selection and companies and limit:
            companies = random.sample(companies, min(limit, len(companies)))
        print(f"{len(companies)} entreprises trouvées dans MongoDB")
    finally:
        client.close()
        return companies


def get_company_by_siret(siret):
    client, collection = get_mongodb_connection(MONGODB_URI, DB_NAME, COLLECTION_NAME)
    company = None
    try:
        company = collection.find_one({"siret": siret})
        if company:
            print(f"Entreprise trouvée avec SIRET {siret}")
        else:
            print(f"Aucune entreprise trouvée avec SIRET {siret}")
    finally:
        client.close()
        return company

def generate_inconsistent_rib_data(original_company, rib_data):
    modified = copy.deepcopy(rib_data)
    inconsistency_types = [
        'titulaire_mismatch',
        'iban_invalid',
        'bic_mismatch',
        'bank_mismatch',
        'account_number_invalid',
        'rib_key_invalid'
    ]

    selected_inconsistencies = random.sample(
        inconsistency_types,
        random.randint(1, min(3, len(inconsistency_types)))
    )
    print(f"Application des incohérences RIB: {selected_inconsistencies}")
    for inconsistency in selected_inconsistencies:
        if inconsistency == 'titulaire_mismatch':
            modified['titulaire'] = fake.name().upper()

        elif inconsistency == 'iban_invalid':
            modified['iban'] = fake.iban().replace('FR', 'FX')
        elif inconsistency == 'bic_mismatch':
            modified['bic'] = fake.swift()
        elif inconsistency == 'bank_mismatch':
            other_banks = [b for b in BANKS if b['name'] != modified['banque']]
            if other_banks:
                new_bank = random.choice(other_banks)
                modified['banque'] = new_bank['name']
                modified['code_banque'] = new_bank['code_banque']
                modified['bic'] = new_bank['bic']

        elif inconsistency == 'account_number_invalid':
            modified['numero_compte'] = fake.numerify('####')
        elif inconsistency == 'rib_key_invalid':
            modified['cle_rib'] = f"{random.randint(0, 99):02d}"
    return modified


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
    denom = company.get("denomination_unite_legale")
    if denom and denom.strip():
        return denom.strip(), "entreprise"
    nom = company.get("nom_unite_legale")
    prenom = company.get("prenom_1_unite_legale") or company.get("prenom_usuel_unite_legale")
    if nom and prenom:
        return f"{prenom.strip()} {nom.strip()}", "personne"
    if nom:
        return nom.strip(), "personne"
    return fake.name().upper(), "inconnu"

def get_address(company):
    adresse_parts = []
    if company.get('numero_voie_etablissement'):
        adresse_parts.append(str(company.get('numero_voie_etablissement')))
    if company.get('type_voie_etablissement'):
        adresse_parts.append(company.get('type_voie_etablissement'))
    if company.get('libelle_voie_etablissement'):
        adresse_parts.append(company.get('libelle_voie_etablissement'))
    adresse = ' '.join(adresse_parts)
    if company.get('code_postal_etablissement') or company.get('libelle_commune_etablissement'):
        ville_parts = []
        if company.get('code_postal_etablissement'):
            ville_parts.append(str(company.get('code_postal_etablissement')))
        if company.get('libelle_commune_etablissement'):
            ville_parts.append(company.get('libelle_commune_etablissement'))
        if ville_parts:
            if adresse:
                adresse += ', ' + ' '.join(ville_parts)
            else:
                adresse = ' '.join(ville_parts)
    if not adresse:
        adresse = company.get('adresse_etablissement', fake.address().replace('\n', ', '))
    return adresse


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
    """Fonction principale avec interface en ligne de commande"""
    parser = argparse.ArgumentParser(description='Génération de RIB depuis MongoDB')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--siret', type=str, help='Générer pour un SIRET spécifique')
    group.add_argument('--sirets', type=str, help='Liste de SIRET séparés par des virgules')
    group.add_argument('--count', type=int, help='Nombre d\'entreprises à générer')
    group.add_argument('--all', action='store_true', help='Générer pour toutes les entreprises')

    parser.add_argument('--filter', type=str,
                        help='Filtre MongoDB au format JSON (ex: \'{"categorie_entreprise":"PME"}\')')
    parser.add_argument('--random', action='store_true', help='Sélection aléatoire')
    parser.add_argument('--inconsistent', action='store_true', help='Générer des RIB incohérents')
    parser.add_argument('--output-dir', type=str, help='Répertoire de sortie personnalisé')

    args = parser.parse_args()

    global OUTPUT_DIR
    if args.output_dir:
        OUTPUT_DIR = args.output_dir
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.siret:
        company = get_company_by_siret(args.siret)
        if company:
            companies = [company]
        else:
            print(f"Erreur: SIRET {args.siret} non trouvé")
            return
    elif args.sirets:
        sirets_list = [s.strip() for s in args.sirets.split(',')]
        companies = get_companies_from_mongodb(sirets=sirets_list)
    elif args.count:
        filters = None
        if args.filter:
            filters = json.loads(args.filter)
        companies = get_companies_from_mongodb(
            limit=args.count,
            filters=filters,
            random_selection=args.random
        )
    elif args.all:
        filters = None
        if args.filter:
            filters = json.loads(args.filter)
        companies = get_companies_from_mongodb(
            filters=filters,
            random_selection=args.random
        )
    else:
        print("Aucune option spécifiée, génération de 10 entreprises aléatoires")
        companies = get_companies_from_mongodb(limit=10, random_selection=True)

    if not companies:
        print("Aucune entreprise trouvée")
        return

    print(f"Génération de {len(companies)} RIB...")

    for i, company in enumerate(companies, 1):
        siret = safe(company.get('siret', fake.numerify('#########')))

        rib_data = generate_rib(company)
        if args.inconsistent:
            rib_data = generate_inconsistent_rib_data(company, rib_data)
        inconsistent_tag = "_inconsistent" if args.inconsistent else ""
        filename = f"rib_{siret}{inconsistent_tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.pdf"
        pdf_path = Path(OUTPUT_DIR) / filename
        print(f"→ {pdf_path}")
        rib_to_pdf(rib_data, str(pdf_path))
    print(f"\n✅ Génération terminée!")
    print(f"📁 {len(companies)} RIB générés dans : {OUTPUT_DIR}")
    if args.inconsistent:
        print("⚠️ Des données incohérentes ont été utilisées")

if __name__ == "__main__":
    main()