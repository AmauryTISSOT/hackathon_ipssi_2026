import os
import random
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from data.utils import get_project_root, safe


ROOT_DIR = get_project_root()
BASE_PATH = os.path.join(ROOT_DIR, "data", "data_sirene")
SILVER_PATH = os.path.join(BASE_PATH, "formatted_data")

execution_date = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = os.path.join(ROOT_DIR, "data", "fake_data", "urssaf_vigilance", execution_date)
os.makedirs(OUTPUT_DIR, exist_ok=True)

fake = Faker("fr_FR")

def random_date_after_creation(company, min_year=1990):
    creation_str = company.get("dateCreationUniteLegale") or company.get("dateCreationEtablissement")

    if not creation_str:
        creation_date = datetime(min_year, 1, 1)
    else:
        try:
            creation_date = datetime.strptime(creation_str, "%Y-%m-%d")
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

    adresse = company.get("adresseEtablissement") or (
        f"{company.get('numeroVoieEtablissement','')} "
        f"{company.get('typeVoieEtablissement','')} "
        f"{company.get('libelleVoieEtablissement','')}, "
        f"{company.get('codePostalEtablissement','')} "
        f"{company.get('libelleCommuneEtablissement','')}"
    )

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
    json_files = list(Path(SILVER_PATH).glob("*.json"))

    if not json_files:
        print(f"Erreur : Aucun fichier JSON trouvé dans : {SILVER_PATH}")
        return

    input_file = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"Fichier sélectionné : {input_file.name}")

    try:
        df_silver = pd.read_json(input_file)
    except Exception as e:
        print(f"Erreur lors de la lecture du JSON : {e}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    limit = min(10, len(df_silver))
    print(f"Génération de {limit} attestations URSSAF...")

    for index, row in df_silver.head(limit).iterrows():
        company = row.to_dict()
        if isinstance(company.get("metadata"), dict):
            company.update(company["metadata"])

        siren = safe(company.get("siren", fake.numerify("#########")))
        att = generate_urssaf_certificate(company)

        pdf_path = Path(OUTPUT_DIR) / f"urssaf_{siren}_{index:03d}.pdf"
        print(f"→ {pdf_path}")

        urssaf_to_pdf_reportlab(att, str(pdf_path))


if __name__ == "__main__":
    main()