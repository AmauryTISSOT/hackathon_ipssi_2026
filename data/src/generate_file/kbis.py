import os
from faker import Faker
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import random
import argparse
import copy

from utils import get_project_root, safe, get_mongodb_connection

fake = Faker('fr_FR')
ROOT_DIR = get_project_root()
load_dotenv(os.path.join(ROOT_DIR, ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "Hackathon")
COLLECTION_NAME = "Company"
BASE_PATH = os.path.join(ROOT_DIR, "data", "data_sirene")
execution_date = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = os.path.join(ROOT_DIR, "data", "fake_data", "kbis_test", execution_date)
os.makedirs(OUTPUT_DIR, exist_ok=True)



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


def get_denomination_or_name(etab_data):
    categorie_juridique = safe(etab_data.get('categorie_juridique_unite_legale', ''))
    if categorie_juridique == '1000':
        nom = safe(etab_data.get('nom_unite_legale', ''))
        prenom = safe(etab_data.get('prenom_1_unite_legale', ''))
        prenom_usuel = safe(etab_data.get('prenom_usuel_unite_legale', ''))
        if nom and prenom:
            if prenom_usuel and prenom_usuel != prenom:
                return f"{nom} {prenom_usuel} ({prenom})"
            return f"{nom} {prenom}"
        elif nom:
            return nom
        elif prenom:
            return prenom
        else:
            return f"{fake.last_name().upper()} {fake.first_name()}"
    else:
        denomination = safe(etab_data.get('denomination_unite_legale'))
        if denomination:
            return denomination
        else:
            return fake.company()


def format_siret_rcs(etab_data):
    siren = safe(etab_data.get('siren', ''))
    siret = safe(etab_data.get('siret', ''))
    ville = safe(etab_data.get('libelle_commune_etablissement', ''))
    if not ville:
        ville = fake.city()
    return {
        'siren': f"{siren} R.C.S. {ville}",
        'siret': siret if siret else f"{siren}{fake.numerify('#####')}"
    }



def get_forme_juridique(etab_data):
    categorie = safe(etab_data.get('categorie_juridique_unite_legale', ''))
    mapping_categories = {
        '1000': 'Entrepreneur individuel',
        '5710': 'SAS, société par actions simplifiée',
        '5720': 'SARL, société à responsabilité limitée',
        '5499': 'SA, société anonyme',
        '5308': 'EURL, entreprise unipersonnelle à responsabilité limitée',
    }
    if categorie and categorie in mapping_categories:
        return mapping_categories[categorie]
    else:
        return fake.random_element(elements=('SAS', 'SARL', 'EURL', 'SA', 'EI'))


def get_adresse_complete(etab_data):
    adresse = safe(etab_data.get('adresse_etablissement', ''))
    complement = safe(etab_data.get('complement_adresse_etablissement', ''))
    numero = safe(etab_data.get('numero_voie_etablissement', ''))
    type_voie = safe(etab_data.get('type_voie_etablissement', ''))
    libelle_voie = safe(etab_data.get('libelle_voie_etablissement', ''))
    code_postal = safe(etab_data.get('code_postal_etablissement', ''))
    commune = safe(etab_data.get('libelle_commune_etablissement', ''))

    if adresse and adresse != 'None':
        return adresse
    parts = []
    if complement and complement != 'None':
        parts.append(complement)
    voie = ''
    if numero and numero != 'None':
        voie += f"{numero} "
    if type_voie and type_voie != 'None':
        voie += f"{type_voie} "
    if libelle_voie and libelle_voie != 'None':
        voie += libelle_voie
    if voie.strip():
        parts.append(voie.strip())
    ville_part = ''
    if code_postal and code_postal != 'None':
        ville_part += code_postal
    if commune and commune != 'None':
        ville_part += f" {commune}" if ville_part else commune
    if ville_part:
        parts.append(ville_part)
    if parts:
        return ' '.join(parts)
    return fake.address().replace('\n', ', ')


def generate_gerant_info(etab_data):
    categorie = safe(etab_data.get('categorie_juridique_unite_legale', ''))

    role = fake.random_element(elements=('Président', 'Directeur Général', 'Gérant', 'Associé unique'))

    if categorie == '1000' and safe(etab_data.get('nom_unite_legale')):
        nom = safe(etab_data.get('nom_unite_legale', '').upper())
        prenom = safe(etab_data.get('prenom_1_unite_legale', ''))
        prenom_usuel = safe(etab_data.get('prenom_usuel_unite_legale', ''))
        if prenom_usuel and prenom_usuel != prenom:
            prenom_aff = f"{prenom_usuel} ({prenom})"
        else:
            prenom_aff = prenom
        lastname = nom
        firstname = prenom_aff
        birth = fake.date_of_birth(minimum_age=25, maximum_age=65).strftime('%d/%m/%Y')
        birth_place = fake.city()
    else:
        lastname = fake.last_name().upper()
        firstname = fake.first_name()
        birth = fake.date_of_birth(minimum_age=25, maximum_age=65).strftime('%d/%m/%Y')
        birth_place = fake.city()

    return {
        'role': role,
        'nom': lastname,
        'prenom': firstname,
        'naissance': f"Le {birth} à {birth_place}",
        "activity": fake.job(),
        'nationalite': "FRANCE",
        'domicile': get_adresse_complete(etab_data)
    }

def generate_inconsistent_company_data(original_company):
    modified = copy.deepcopy(original_company)
    inconsistency_types = [
        'name_mismatch',
        'address_mismatch',
        'capital_mismatch',
        'manager_mismatch',
        'date_mismatch',
        'siren_siret_mismatch'
    ]
    selected_inconsistencies = random.sample(
        inconsistency_types,
        random.randint(1, min(3, len(inconsistency_types)))
    )
    print(f"Application des incohérences: {selected_inconsistencies}")
    for inconsistency in selected_inconsistencies:
        if inconsistency == 'name_mismatch':
            if 'denomination_unite_legale' in modified:
                modified['denomination_unite_legale'] = fake.company()
            else:
                modified['denomination_unite_legale'] = fake.company()
        elif inconsistency == 'address_mismatch':
            modified['adresse_etablissement'] = fake.address().replace('\n', ', ')
            modified['code_postal_etablissement'] = fake.postcode()
            modified['libelle_commune_etablissement'] = fake.city()
        elif inconsistency == 'capital_mismatch':
            modified['capital_social'] = fake.random_int(min=100, max=10000000)
        elif inconsistency == 'manager_mismatch':
            if 'manager' in modified:
                modified['manager']['nom'] = fake.last_name().upper()
                modified['manager']['prenom'] = fake.first_name()
                modified['manager']['fonction'] = random.choice([
                    'PDG', 'DG', 'Gérant', 'Président', 'Secrétaire général'
                ])
            else:
                modified['manager'] = {
                    'nom': fake.last_name().upper(),
                    'prenom': fake.first_name(),
                    'fonction': random.choice(['PDG', 'DG', 'Gérant', 'Président']),
                    'date_naissance': datetime.combine(
                        fake.date_of_birth(minimum_age=25, maximum_age=65),
                        datetime.min.time()
                    ),
                    "activity": fake.job(),
                    'lieu_naissance': fake.city(),
                    'nationalite': 'FRANCE'
                }
        elif inconsistency == 'date_mismatch':
            modified['date_creation_unite_legale'] = fake.date_between(
                start_date='-20y', end_date='-1y'
            ).strftime('%Y-%m-%d')

        elif inconsistency == 'siren_siret_mismatch':
            if 'siren' in modified and 'siret' in modified:
                new_siren = fake.numerify('#########')
                modified['siren'] = new_siren
                modified['siret'] = new_siren + fake.numerify('#####')
    return modified


def draw_header(c, margin, y, num_gestion):
    c.setFont('Helvetica', 9)
    greffe_lignes = [
        f"Greffe du tribunal de commerce de {fake.city()}",
        fake.address().replace('\n', ', '),
        f"N° de gestion : {num_gestion}"
    ]
    x_left = margin
    for i, ligne in enumerate(greffe_lignes):
        c.drawString(x_left, y - i * 5 * mm, ligne)
    return y - 25 * mm


def draw_title_section(c, width, y):
    c.setFont('Helvetica-Bold',10)
    titre1 = "EXTRAIT KBIS"
    titre1_width = c.stringWidth(titre1, 'Helvetica-Bold', 10)
    c.drawString((width - titre1_width) / 2, y, titre1)
    y -= 8 * mm

    c.setFont('Helvetica-Bold', 14)
    titre2 = "EXTRAIT D'IMMATRICULATION PRINCIPALE AU REGISTRE DU COMMERCE"
    titre2_width = c.stringWidth(titre2, 'Helvetica-Bold', 14)
    c.drawString((width - titre2_width) / 2, y, titre2)
    y -= 5 * mm
    titre3 = "ET DES SOCIÉTÉS"
    titre3_width = c.stringWidth(titre3, 'Helvetica-Bold', 14)
    c.drawString((width - titre3_width) / 2, y, titre3)
    y -= 5 * mm

    c.setFont('Helvetica', 9)
    date_jour = f"À jour au {fake.date_this_month().strftime('%d/%m/%Y')}"
    date_width = c.stringWidth(date_jour, 'Helvetica', 9)
    c.drawString((width - date_width) / 2, y, date_jour)
    y -= 10 * mm

    return y


def draw_section_header(c, x, y, width, margin, titre):
    c.setFont('Helvetica-Bold', 11)
    c.drawString(x, y, titre)
    y -= 2 * mm
    c.line(margin, y, width - margin, y)
    return y - 5 * mm

def draw_field_row(c, y, label, value, x_label, x_value, max_width):
    c.setFont('Helvetica', 10)

    c.drawString(x_label, y, label)

    c.setFont('Helvetica', 10)
    lines = simpleSplit(str(value), 'Helvetica', 10, max_width)

    for i, line in enumerate(lines):
        c.drawString(x_value, y - i * 5 * mm, line)

    return len(lines) * 5 * mm

def generate_kbis_pdf_from_company(company_data, output_path, use_inconsistent=False):
    if use_inconsistent:
        etab_data = generate_inconsistent_company_data(company_data)
        print(f"Génération d'un KBIS incohérent pour {etab_data.get('denomination_unite_legale', 'N/A')}")
    else:
        etab_data = company_data.copy()
    manager_data = etab_data.get('manager', {})
    if manager_data:
        etab_data['nomUniteLegale'] = manager_data.get('nom', '')
        etab_data['prenom1UniteLegale'] = manager_data.get('prenom', '')
        etab_data['sexeUniteLegale'] = manager_data.get('sexe', '')
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    line_height = 5 * mm
    y = height - margin
    num_gestion = f"{fake.numerify('####')}{fake.random_letter().upper()}{fake.numerify('#####')}"
    y = draw_header(c, margin, y, num_gestion)
    y = draw_title_section(c, width, y)
    denomination = get_denomination_or_name(etab_data)
    siret_info = format_siret_rcs(etab_data)
    forme_juridique = get_forme_juridique(etab_data)
    adresse = get_adresse_complete(etab_data)
    y = draw_section_header(c, margin, y, width, margin, "IDENTIFICATION DE LA PERSONNE MORALE")
    x_label = margin
    x_value = margin + 50 * mm
    max_width = width - x_value - margin
    y -= draw_field_row(c, y, "Dénomination / Nom", denomination, x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Numéro SIREN", siret_info['siren'], x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Numéro SIRET", siret_info['siret'], x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Forme juridique", forme_juridique, x_label, x_value, max_width)
    capital = etab_data.get('capital_social', fake.random_int(min=1000, max=50000))
    y -= draw_field_row(c, y, "Capital social", f"{capital} €", x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Adresse du siège", adresse, x_label, x_value, max_width)
    activite = safe(etab_data.get('activite_principale_unite_legale', 'Non renseignée'))
    y -= draw_field_row(c, y, "Code NAF / APE", activite, x_label, x_value, max_width)
    expiry = fake.date_between(start_date='+50y', end_date='+99y').strftime('%d/%m/%Y')
    y -= draw_field_row(c, y, "Durée de la société", f"Jusqu'au {expiry}", x_label, x_value, max_width)
    y -= line_height
    y = draw_section_header(c, margin, y, width, margin, "GESTION, DIRECTION, ADMINISTRATION, CONTRÔLE")
    if manager_data:
        y -= draw_field_row(c, y, "Fonction", manager_data.get('fonction', 'Gérant'), x_label, x_value, max_width)
        y -= draw_field_row(c, y, "Nom", manager_data.get('nom', ''), x_label, x_value, max_width)
        y -= draw_field_row(c, y, "Prénoms", manager_data.get('prenom', ''), x_label, x_value, max_width)
        birth_date = manager_data.get('date_naissance')
        if birth_date:
            if isinstance(birth_date, datetime):
                birth_str = birth_date.strftime('%d/%m/%Y')
            else:
                birth_str = str(birth_date)
        else:
            birth_str = fake.date_of_birth(minimum_age=25, maximum_age=65).strftime('%d/%m/%Y')
        birth_place = manager_data.get('lieu_naissance', fake.city())
        naissance = f"Le {birth_str} à {birth_place}"
        y -= draw_field_row(c, y, "Date et lieu de naissance", naissance, x_label, x_value, max_width)
        nationalite = manager_data.get('nationalite', "FRANCE")
        y -= draw_field_row(c, y, "Nationalité", nationalite, x_label, x_value, max_width)
        domicile = manager_data.get('adresse', get_adresse_complete(etab_data))
        y -= draw_field_row(c, y, "Domicile", domicile, x_label, x_value, max_width)
    else:
        gerant = generate_gerant_info(etab_data)
        y -= draw_field_row(c, y, "Fonction", gerant['role'], x_label, x_value, max_width)
        y -= draw_field_row(c, y, "Nom", gerant['nom'], x_label, x_value, max_width)
        y -= draw_field_row(c, y, "Prénoms", gerant['prenom'], x_label, x_value, max_width)
        y -= draw_field_row(c, y, "Date et lieu de naissance", gerant['naissance'], x_label, x_value, max_width)
        y -= draw_field_row(c, y, "Nationalité", gerant['nationalite'], x_label, x_value, max_width)
        y -= draw_field_row(c, y, "Domicile", gerant['domicile'], x_label, x_value, max_width)
    y -= line_height
    y = draw_section_header(c, margin, y, width, margin, "RENSEIGNEMENTS RELATIFS À L'ACTIVITÉ ET L'ÉTABLISSEMENT")
    y -= draw_field_row(c, y, "Adresse établissement", adresse, x_label, x_value, max_width)
    activite_exercee = safe(manager_data.get("activity"))
    y -= draw_field_row(c, y, "Activité exercée ", activite_exercee, x_label, x_value, max_width)
    date_creation = safe(etab_data.get('date_creation_unite_legale', ''))
    if not date_creation or date_creation == '':
        date_creation = fake.date_between(start_date='-10y', end_date='-1y').strftime('%Y-%m-%d')
    try:
        if isinstance(date_creation, datetime):
            date_creation_formatee = date_creation.strftime('%d/%m/%Y')
        else:
            date_creation_formatee = datetime.strptime(str(date_creation), '%Y-%m-%d').strftime('%d/%m/%Y')
    except:
        date_creation_formatee = str(date_creation)
    y -= draw_field_row(c, y, "Date de début d'activité", date_creation_formatee, x_label, x_value, max_width)
    date_immat = fake.date_between(start_date='-5y', end_date='-1d').strftime('%d/%m/%Y')
    y -= draw_field_row(c, y, "Date d'immatriculation", date_immat, x_label, x_value, max_width)
    date_modif = fake.date_between(start_date='-1y', end_date='today').strftime('%d/%m/%Y')
    y -= draw_field_row(c, y, "Dernière modification", date_modif, x_label, x_value, max_width)
    footer_y = margin + 10 * mm
    date_delivrance = fake.date_between(start_date='-3y', end_date='today').strftime('%d/%m/%Y')
    footer_text = f"Extrait délivré le {date_delivrance} - Fin de l'extrait"
    c.setFont('Helvetica-Oblique', 8)
    c.drawCentredString(width / 2, footer_y, footer_text)
    c.save()
    print(f"Kbis généré pour {denomination} (SIREN: {safe(etab_data.get('siren', 'N/A'))})")

def main():
    parser = argparse.ArgumentParser(description='Génération de KBIS depuis MongoDB')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--siret', type=str, help='Générer pour un SIRET spécifique')
    group.add_argument('--sirets', type=str, help='Liste de SIRET séparés par des virgules')
    group.add_argument('--count', type=int, help='Nombre d\'entreprises à générer')
    group.add_argument('--all', action='store_true', help='Générer pour toutes les entreprises')
    parser.add_argument('--filter', type=str,
                        help='Filtre MongoDB au format JSON (ex: \'{"categorie_entreprise":"PME"}\')')
    parser.add_argument('--random', action='store_true', help='Sélection aléatoire')
    parser.add_argument('--inconsistent', action='store_true', help='Générer des KBIS incohérents')
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
        siret_list = [s.strip() for s in args.sirets.split(',')]
        companies = get_companies_from_mongodb(sirets=siret_list)
    elif args.count:
        filters = None
        if args.filter:
            import json
            filters = json.loads(args.filter)
        companies = get_companies_from_mongodb(
            limit=args.count,
            filters=filters,
            random_selection=args.random
        )
    elif args.all:
        filters = None
        if args.filter:
            import json
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
    print(f"Génération de {len(companies)} KBIS...")

    for i, company in enumerate(companies, 1):
        siren = safe(company.get('siren', fake.numerify('#########')))
        inconsistent_tag = "_inconsistent" if args.inconsistent else ""
        filename = f"kbis_{siren}{inconsistent_tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.pdf"
        generate_kbis_pdf_from_company(
            company,
            os.path.join(OUTPUT_DIR, filename),
            use_inconsistent=args.inconsistent
        )
    print(f"\nGénération terminée!")
    print(f"{len(companies)} fichiers KBIS générés dans : {OUTPUT_DIR}")
    if args.inconsistent:
        print("Des données incohérentes ont été utilisées")


if __name__ == "__main__":
    main()