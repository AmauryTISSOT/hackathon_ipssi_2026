import os
import random
from datetime import date, timedelta
from faker import Faker
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

fake = Faker("fr_FR")

OUTPUT_DIR = "fake_data/factures"
NUM_FACTURES = 10

TVA_RATE = 0.20
CURRENCY = "€"

PAYMENT_METHODS = ["Virement bancaire", "Chèque", "Prélèvement automatique", "Carte bancaire"]

SERVICES = [
    ("Développement web", 80, 150),
    ("Développement mobile", 90, 160),
    ("Design UI/UX", 60, 120),
    ("Conseil IT", 100, 200),
    ("Maintenance applicative", 50, 90),
    ("Audit de sécurité", 120, 250),
    ("Formation", 70, 130),
    ("Intégration API", 85, 140),
    ("Migration cloud", 110, 180),
    ("Data engineering", 95, 170),
]

# Génération du numéro de facture en utilisant la date actuelle
def generate_facture_number(index: int) -> str:
    year = date.today().year
    return f"FAC-{year}-{index:04d}"

# Génération des items dans le tableau
def generate_line_items() -> list[dict]:
    n = random.randint(2, 6)
    items = []
    for _ in range(n):
        label, price_min, price_max = random.choice(SERVICES)
        qty = random.randint(1, 20)
        unit_price = round(random.uniform(price_min, price_max), 2)
        items.append({
            "description": label,
            "qty": qty,
            "unit": "h",
            "unit_price": unit_price,
            "total_ht": round(qty * unit_price, 2),
        })
    return items

# Génération des données de la facture
def generate_facture_data(index: int) -> dict:
    issue_date = fake.date_between(start_date="-90d", end_date="today")
    due_days = random.choice([30, 45, 60])
    due_date = issue_date + timedelta(days=due_days)

    items = generate_line_items()
    total_ht = round(sum(i["total_ht"] for i in items), 2)
    tva = round(total_ht * TVA_RATE, 2)
    total_ttc = round(total_ht + tva, 2)

    return {
        "number": generate_facture_number(index),
        "issue_date": issue_date.strftime("%d/%m/%Y"),
        "due_date": due_date.strftime("%d/%m/%Y"),
        "payment_method": random.choice(PAYMENT_METHODS),
        "seller": {
            "company": fake.company(),
            "address": fake.address().replace("\n", ", "),
            "email": fake.company_email(),
            "phone": fake.phone_number(),
            "siret": fake.siret(),
            "iban": fake.iban(),
            "tva_intra": f"FR{random.randint(10, 99)}{fake.siret()[:9].replace(' ', '')}",
        },
        "client": {
            "company": fake.company(),
            "contact": fake.name(),
            "address": fake.address().replace("\n", ", "),
            "email": fake.email(),
            "siret": fake.siret(),
        },
        "items": items,
        "total_ht": total_ht,
        "tva": tva,
        "total_ttc": total_ttc,
    }

# Création du PDF
def build_pdf(data: dict, filepath: str) -> None:

    # Déclaration du format du PDF
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    # Déclaration des styles
    title_style = ParagraphStyle(
        "title", fontSize=20, fontName="Helvetica-Bold", spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "subtitle", fontSize=9, fontName="Helvetica", textColor=colors.grey
    )
    section_style = ParagraphStyle(
        "section", fontSize=10, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=8
    )
    body_style = ParagraphStyle("body", fontSize=9, fontName="Helvetica", leading=13)

    primary = colors.HexColor("#2e7d32")   # vert — différencie visuellement la facture du devis
    light_bg = colors.HexColor("#f1f8f1")

    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    header_data = [
        [
            Paragraph(f"<b>{data['seller']['company']}</b>", title_style),
            Paragraph(
                f"<b>FACTURE N° {data['number']}</b>",
                ParagraphStyle("facnum", fontSize=16, fontName="Helvetica-Bold",
                               alignment=2, textColor=primary),
            ),
        ],
        [
            Paragraph(data["seller"]["address"], body_style),
            Paragraph(
                f"Date : {data['issue_date']}<br/>Échéance : {data['due_date']}",
                ParagraphStyle("info", fontSize=9, fontName="Helvetica", alignment=2),
            ),
        ],
        [
            Paragraph(
                f"{data['seller']['email']} | {data['seller']['phone']}", subtitle_style
            ),
            Paragraph(
                f"SIRET : {data['seller']['siret']}<br/>TVA : {data['seller']['tva_intra']}",
                ParagraphStyle("siret", fontSize=8, fontName="Helvetica",
                               textColor=colors.grey, alignment=2),
            ),
        ],
    ]

    header_table = Table(header_data, colWidths=[95 * mm, 75 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 2), (-1, 2), 0.5, colors.lightgrey),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8 * mm))

    # ── Client ──────────────────────────────────────────────────────────────
    story.append(Paragraph("FACTURÉ À", section_style))
    client = data["client"]
    story.append(Paragraph(
        f"<b>{client['company']}</b><br/>"
        f"À l'attention de : {client['contact']}<br/>"
        f"{client['address']}<br/>"
        f"{client['email']}<br/>"
        f"SIRET : {client['siret']}",
        body_style,
    ))
    story.append(Spacer(1, 8 * mm))

    # ── Tableau des prestations ──────────────────────────────────────────────
    story.append(Paragraph("DÉTAIL DES PRESTATIONS", section_style))

    col_headers = ["Description", "Qté", "Unité", "Prix unit. HT", "Total HT"]
    table_data = [col_headers]
    for item in data["items"]:
        table_data.append([
            item["description"],
            str(item["qty"]),
            item["unit"],
            f"{item['unit_price']:.2f} {CURRENCY}",
            f"{item['total_ht']:.2f} {CURRENCY}",
        ])

    col_widths = [80 * mm, 18 * mm, 18 * mm, 32 * mm, 32 * mm]
    items_table = Table(table_data, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (-2, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 6 * mm))

    # ── Totaux ───────────────────────────────────────────────────────────────
    totals_data = [
        ["", "Total HT :", f"{data['total_ht']:.2f} {CURRENCY}"],
        ["", f"TVA ({int(TVA_RATE * 100)}%) :", f"{data['tva']:.2f} {CURRENCY}"],
        ["", "Total TTC :", f"{data['total_ttc']:.2f} {CURRENCY}"],
    ]
    totals_table = Table(totals_data, colWidths=[98 * mm, 40 * mm, 32 * mm])
    totals_table.setStyle(TableStyle([
        ("FONTNAME", (1, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (1, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LINEABOVE", (1, 2), (-1, 2), 0.8, primary),
        ("TEXTCOLOR", (1, 2), (-1, 2), primary),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 10 * mm))

    # ── Informations de paiement ──────────────────────────────────────────────
    story.append(Paragraph("INFORMATIONS DE PAIEMENT", section_style))
    story.append(Paragraph(
        f"Mode de règlement : {data['payment_method']}<br/>"
        f"IBAN : {data['seller']['iban']}<br/>"
        f"À régler avant le : <b>{data['due_date']}</b><br/>"
        f"Pas d'escompte pour règlement anticipé.",
        body_style,
    ))
    story.append(Spacer(1, 10 * mm))

    # ── Footer ──────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "En cas de retard de paiement, des pénalités de retard au taux de 3 fois le taux "
        "d'intérêt légal en vigueur seront appliquées (art. L441-10 du Code de commerce), "
        "ainsi qu'une indemnité forfaitaire de recouvrement de 40 € (art. D441-5).",
        ParagraphStyle("note", fontSize=8, fontName="Helvetica-Oblique",
                       textColor=colors.grey),
    ))

    doc.build(story)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for i in range(1, NUM_FACTURES + 1):
        data = generate_facture_data(i)
        filepath = os.path.join(OUTPUT_DIR, f"{data['number']}.pdf")
        build_pdf(data, filepath)
        print(f"[{i:02d}/{NUM_FACTURES}] Générée : {filepath}")
    print(f"\n✓ {NUM_FACTURES} factures créées dans le dossier « {OUTPUT_DIR}/»")


if __name__ == "__main__":
    main()
