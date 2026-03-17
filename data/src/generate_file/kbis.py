import os
import pandas as pd
from faker import Faker
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from pathlib import Path
from datetime import datetime

from data.data_sirene.utils.utils import get_project_root

fake = Faker('fr_FR')


ROOT_DIR = get_project_root()
BASE_PATH = os.path.join(ROOT_DIR, "data", "data_sirene")
SILVER_PATH = os.path.join(BASE_PATH, "formatted_data")
BASE_FAKE_PATH = os.path.join(BASE_PATH, "fake_data")
execution_date = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = os.path.join(ROOT_DIR, "data", "fake_data", "kbis", execution_date)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_denomination_or_name(etab_data):
    categorie_juridique = etab_data.get('categorieJuridiqueUniteLegale', '')
    if categorie_juridique == '1000':
        nom = etab_data.get('nomUniteLegale', '')
        prenom = etab_data.get('prenom1UniteLegale', '')
        prenom_usuel = etab_data.get('prenomUsuelUniteLegale', '')

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
        denomination = etab_data.get('denominationUniteLegale')
        if denomination:
            return denomination
        else:
            return fake.company()


def format_siret_rcs(etab_data):
    siren = etab_data.get('siren', '')
    siret = etab_data.get('siret', '')
    ville = etab_data.get('libelleCommuneEtablissement', '')
    if not ville:
        ville = fake.city()
    return {
        'siren': f"{siren} R.C.S. {ville}",
        'siret': siret if siret else f"{siren}{fake.numerify('#####')}"
    }

def get_forme_juridique(etab_data):
    categorie = etab_data.get('categorieJuridiqueUniteLegale', '')
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
    adresse = etab_data.get('adresseEtablissement', '')
    complement = etab_data.get('complementAdresseEtablissement', '')
    numero = etab_data.get('numeroVoieEtablissement', '')
    type_voie = etab_data.get('typeVoieEtablissement', '')
    libelle_voie = etab_data.get('libelleVoieEtablissement', '')
    code_postal = etab_data.get('codePostalEtablissement', '')
    commune = etab_data.get('libelleCommuneEtablissement', '')

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
    categorie = etab_data.get('categorieJuridiqueUniteLegale', '')

    role = fake.random_element(elements=('Président', 'Directeur Général', 'Gérant', 'Associé unique'))

    if categorie == '1000' and etab_data.get('nomUniteLegale'):
        nom = etab_data.get('nomUniteLegale', '').upper()
        prenom = etab_data.get('prenom1UniteLegale', '')
        prenom_usuel = etab_data.get('prenomUsuelUniteLegale', '')
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
        'nationalite': "FRANCAIS",
        'domicile': fake.address().replace('\n', ', ')
    }


def create_siege_social_if_needed(etab_data):
    est_siege = etab_data.get('etablissementSiege', False)

    if not est_siege:
        siege_data = etab_data.copy()
        siege_data['adresseEtablissement'] = fake.address().replace('\n', ', ')
        siege_data['libelleCommuneEtablissement'] = fake.city()
        siege_data['codePostalEtablissement'] = fake.postcode()
        siege_data['etablissementSiege'] = True
        print(f"⚠️ Établissement non siège, génération d'un siège fictif à {siege_data['libelleCommuneEtablissement']}")
        return siege_data

    return etab_data


def draw_header(c, width, margin, y, num_gestion):
    c.setFont('Helvetica', 9)
    greffe_lignes = [
        f"Greffe du tribunal de commerce de {fake.city()}",
        fake.address().replace('\n', ', ')[:40],
        f"N° de gestion : {num_gestion}"
    ]
    x_left = margin
    for i, ligne in enumerate(greffe_lignes):
        c.drawString(x_left, y - i * 5 * mm, ligne)

    return y - 25 * mm


def draw_title_section(c, width, margin, y):
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


def generate_kbis_pdf(etab_data, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    line_height = 5 * mm

    y = height - margin
    num_gestion = f"{fake.numerify('####')}{fake.random_letter().upper()}{fake.numerify('#####')}"

    y = draw_header(c, width, margin, y, num_gestion)

    y = draw_title_section(c, width, margin, y)

    etab_a_utiliser = create_siege_social_if_needed(etab_data)

    denomination = get_denomination_or_name(etab_a_utiliser)
    siret_info = format_siret_rcs(etab_a_utiliser)
    forme_juridique = get_forme_juridique(etab_a_utiliser)
    adresse = get_adresse_complete(etab_a_utiliser)

    y = draw_section_header(c, margin, y, width, margin, "IDENTIFICATION DE LA PERSONNE MORALE")

    x_label = margin
    x_value = margin + 50 * mm
    max_width = width - x_value - margin

    y -= draw_field_row(c, y, "Dénomination / Nom", denomination, x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Numéro SIREN", siret_info['siren'], x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Numéro SIRET", siret_info['siret'], x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Forme juridique", forme_juridique, x_label, x_value, max_width)
    capital = fake.random_int(min=1000, max=50000)
    y -= draw_field_row(c, y, "Capital social", f"{capital} €", x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Adresse du siège", adresse, x_label, x_value, max_width)
    activite = etab_a_utiliser.get('activitePrincipaleUniteLegale', 'Non renseignée')
    y -= draw_field_row(c, y, "Code NAF / APE", activite, x_label, x_value, max_width)
    expiry = fake.date_between(start_date='+50y', end_date='+99y').strftime('%d/%m/%Y')
    y -= draw_field_row(c, y, "Durée de la société", f"Jusqu'au {expiry}", x_label, x_value, max_width)
    y -= line_height
    y = draw_section_header(c, margin, y, width, margin, "GESTION, DIRECTION, ADMINISTRATION, CONTRÔLE")
    gerant = generate_gerant_info(etab_a_utiliser)
    y -= draw_field_row(c, y, "Fonction", gerant['role'], x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Nom", gerant['nom'], x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Prénoms", gerant['prenom'], x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Date et lieu de naissance", gerant['naissance'], x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Nationalité", gerant['nationalite'], x_label, x_value, max_width)
    y -= draw_field_row(c, y, "Domicile", gerant['domicile'], x_label, x_value, max_width)
    y -= line_height
    y = draw_section_header(c, margin, y, width, margin, "RENSEIGNEMENTS RELATIFS À L'ACTIVITÉ ET L'ÉTABLISSEMENT")
    y -= draw_field_row(c, y, "Adresse établissement", adresse, x_label, x_value, max_width)
    activite_exercee = fake.catch_phrase()
    y -= draw_field_row(c, y, "Activité exercée ", activite_exercee, x_label, x_value, max_width)
    date_creation = etab_a_utiliser.get('dateCreationEtablissement', '')
    if not date_creation or date_creation == '2000-01-01':
        date_creation = fake.date_between(start_date='-10y', end_date='-1y').strftime('%Y-%m-%d')
    try:
        date_creation_formatee = datetime.strptime(date_creation, '%Y-%m-%d').strftime('%d/%m/%Y')
    except:
        date_creation_formatee = date_creation
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
    print(f"✅ Kbis généré pour {denomination} (SIREN: {etab_a_utiliser.get('siren', 'N/A')})")


def run_kbis_generation():
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

    df_silver = df_silver[df_silver['etatAdministratifUniteLegale'] == 'C']

    limit = min(10, len(df_silver))
    print(f"Génération de {limit} fichiers Kbis...")

    for index, row in df_silver.head(limit).iterrows():
        etab_data = row.to_dict()

        if 'metadata' in etab_data and isinstance(etab_data['metadata'], dict):
            etab_data.update(etab_data['metadata'])

        siren = etab_data.get('siren', fake.numerify('#########'))
        filename = f"kbis_{siren}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        generate_kbis_pdf(etab_data, os.path.join(OUTPUT_DIR, filename))

    print(f"Terminé. {limit} fichiers générés dans : {OUTPUT_DIR}")


if __name__ == "__main__":
    run_kbis_generation()