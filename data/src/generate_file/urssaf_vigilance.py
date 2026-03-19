import copy
import os
import random
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta

from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from dotenv import load_dotenv
from pymongo import MongoClient

from utils import get_project_root, safe, get_mongodb_connection

ROOT_DIR = get_project_root()
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Configuration MongoDB
_mongo_user = os.getenv("MONGO_ROOT_USER", "")
_mongo_password = os.getenv("MONGO_ROOT_PASSWORD", "")
_mongo_host = os.getenv("MONGODB_HOST", "localhost:27017")
MONGODB_URI = f"mongodb://{_mongo_user}:{_mongo_password}@{_mongo_host}" if _mongo_user else f"mongodb://{_mongo_host}"
DB_NAME = os.getenv("DB_NAME", "Hackathon")
COLLECTION_NAME = "companies"

execution_date = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = os.path.join(ROOT_DIR, "data", "fake_data", "urssaf_vigilance", execution_date)
os.makedirs(OUTPUT_DIR, exist_ok=True)

fake = Faker("fr_FR")


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


def generate_inconsistent_urssaf_data(urssaf_data):
    modified = copy.deepcopy(urssaf_data)

    inconsistency_types = [
        'siren_mismatch',
        'siret_mismatch',
        'date_mismatch',
        'security_code_invalid',
        'address_mismatch',
        'identifier_mismatch'
    ]

    selected_inconsistencies = random.sample(
        inconsistency_types,
        random.randint(1, min(3, len(inconsistency_types)))
    )
    print(f"Application des incohérences URSSAF: {selected_inconsistencies}")
    for inconsistency in selected_inconsistencies:
        if inconsistency == 'siren_mismatch':
            modified['siren'] = fake.numerify('#########')
        elif inconsistency == 'siret_mismatch':
            modified['siret'] = fake.numerify('##############')
        elif inconsistency == 'date_mismatch':
            if random.choice([True, False]):
                modified['created_at'] = (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d')
            else:
                modified['created_at'] = fake.date_between(start_date='-30y', end_date='-20y').strftime('%Y-%m-%d')
        elif inconsistency == 'security_code_invalid':
            modified['security_code'] = fake.bothify("??##-??##").upper()
            if random.choice([True, False]):
                modified['security_code'] = modified['security_code'].replace('-', '')
        elif inconsistency == 'address_mismatch':
            modified['activity_address'] = fake.address().replace('\n', ', ')
        elif inconsistency == 'identifier_mismatch':
            modified['internal_identifier'] = f"URSSAF-{random.randint(0, 999)}"

    return modified


def random_date_after_creation(company, min_year=1990):
    creation_str = company.get("date_creation_unite_legale") or company.get("date_creation_etablissement")
    if not creation_str:
        creation_date = datetime(min_year, 1, 1)
    else:
        try:
            if isinstance(creation_str, datetime):
                creation_date = creation_str
            else:
                creation_date = datetime.strptime(str(creation_str), "%Y-%m-%d")
        except Exception:
            creation_date = datetime(min_year, 1, 1)
    if creation_date.year < min_year:
        creation_date = datetime(min_year, 1, 1)
    end_date = datetime.now()
    delta = end_date - creation_date
    random_days = random.randint(0, delta.days)
    return (creation_date + timedelta(days=random_days)).strftime("%Y-%m-%d")


def generate_urssaf_certificate(company):
    siren = company.get("siren")
    siret = company.get("siret")
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

    return {
        "siren": siren,
        "siret": siret,
        "social_security": fake.ssn(),
        "internal_identifier": f"URSSAF-{random.randint(100000, 999999)}",
        "security_code": fake.bothify("??##-??##").upper(),
        "created_at": random_date_after_creation(company),

        "place_at": fake.city(),
        "activity_address": adresse
    }


def urssaf_to_pdf_reportlab(att, filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    c.setFillColorRGB(0, 0.35, 0.65)
    c.rect(0, height - 25 * mm, width, 18 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(15 * mm, height - 14 * mm, "Urssaf")
    c.setFont("Helvetica", 9)
    c.drawString(15 * mm, height - 19 * mm, "Au service de la protection sociale")
    info_x = width - 70 * mm
    info_y = height - 14 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(info_x, info_y, "Informations URSSAF :")
    info_y -= 4.5 * mm
    c.setFont("Helvetica", 8)
    c.drawString(info_x, info_y, "Téléphone : 3698")
    info_y -= 4.5 * mm
    c.drawString(info_x, info_y, "Site : www.urssaf.fr")
    info_y -= 4.5 * mm
    c.drawString(info_x, info_y, f"Code sécurité : {att['security_code']}")
    info_y -= 4.5 * mm
    c.drawString(info_x, info_y, f"Identifiant : {att['internal_identifier']}")

    c.setFillColor(colors.black)
    c.setStrokeColorRGB(0, 0.35, 0.65)
    c.setLineWidth(3)
    c.line(12 * mm, 20 * mm, 12 * mm, height - 20 * mm)

    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(width / 2, height - 55 * mm, "ATTESTATION DE VIGILANCE")
    margin_left = 45 * mm
    y = height - 75 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left, y, "Cadre légal :")
    y -= 5 * mm

    c.setFont("Helvetica", 8.5)
    c.drawString(margin_left, y, "Articles L.8222-1 à L.8222-3 et D.8222-5 du Code du Travail.")
    y -= 4.5 * mm
    c.drawString(margin_left, y, "La validité de ce document peut être vérifiée sur le site de l'URSSAF.")
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left, y, "Informations de l'entreprise :")
    y -= 6 * mm

    c.setFont("Helvetica", 8.5)
    c.drawString(margin_left, y, f"SIREN : {att['siren']}")
    y -= 4.5 * mm
    c.drawString(margin_left, y, f"SIRET : {att['siret']}")
    y -= 4.5 * mm
    c.drawString(margin_left, y, f"N° Sécurité Sociale : {att['social_security']}")
    y -= 6 * mm

    c.drawString(margin_left, y, "Adresse d'activité :")
    y -= 4.5 * mm
    for line in att["activity_address"].split(","):
        c.drawString(margin_left + 6 * mm, y, line.strip())
        y -= 4.5 * mm

    y -= 8 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left, y, "Certification :")
    y -= 6 * mm

    c.setFont("Helvetica", 8.5)
    c.drawString(
        margin_left,
        y,
        "L'URSSAF certifie que l'entreprise mentionnée ci-dessus est à jour de ses obligations."
    )
    y -= 12 * mm

    c.drawString(margin_left, y, f"Fait à : {att['place_at']}")
    y -= 4.5 * mm
    c.drawString(margin_left, y, f"Le : {att['created_at']}")
    y -= 8 * mm

    c.setFont("Helvetica-Oblique", 10)
    c.drawString(margin_left, y, "Le Directeur,")
    y -= 7 * mm

    c.setFont("Helvetica", 9)
    c.drawString(margin_left + 5 * mm, y, fake.name())

    qr_data = f"SIREN:{att['siren']}|SIRET:{att['siret']}|CODE:{att['security_code']}"
    qr_code = qr.QrCodeWidget(qr_data)
    bounds = qr_code.getBounds()
    size = 22 * mm
    w = bounds[2] - bounds[0]
    h = bounds[3] - bounds[1]

    d = Drawing(size, size, transform=[size / w, 0, 0, size / h, 0, 0])
    d.add(qr_code)

    renderPDF.draw(d, c, width - 40 * mm, 25 * mm)

    c.save()


def main():
    """Fonction principale avec interface en ligne de commande"""
    global OUTPUT_DIR
    parser = argparse.ArgumentParser(description='Génération d\'attestations URSSAF depuis MongoDB')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--siret', type=str, help='Générer pour un SIRET spécifique')
    group.add_argument('--sirets', type=str, help='Liste de SIRET séparés par des virgules')
    group.add_argument('--count', type=int, help='Nombre d\'entreprises à générer')
    group.add_argument('--all', action='store_true', help='Générer pour toutes les entreprises')
    parser.add_argument('--filter', type=str,help='Filtre MongoDB au format JSON (ex: \'{"categorie_entreprise":"PME"}\')')
    parser.add_argument('--random', action='store_true', help='Sélection aléatoire')
    parser.add_argument('--inconsistent', action='store_true', help='Générer des attestations incohérentes')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR, help='Répertoire de sortie personnalisé')
    args = parser.parse_args()
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

    print(f"Génération de {len(companies)} attestations URSSAF...")

    for i, company in enumerate(companies, 1):
        siren = safe(company.get('siren', fake.numerify('#########')))

        urssaf_data = generate_urssaf_certificate(company)

        if args.inconsistent:
            urssaf_data = generate_inconsistent_urssaf_data(urssaf_data)

        inconsistent_tag = "_inconsistent" if args.inconsistent else ""
        filename = f"urssaf_{siren}{inconsistent_tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.pdf"

        pdf_path = Path(OUTPUT_DIR) / filename
        print(f"→ {pdf_path}")

        urssaf_to_pdf_reportlab(urssaf_data, str(pdf_path))

    print(f"\nGénération terminée!")
    print(f"{len(companies)} attestations URSSAF générées dans : {OUTPUT_DIR}")
    if args.inconsistent:
        print("Des données incohérentes ont été utilisées")


if __name__ == "__main__":
    main()