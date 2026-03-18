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

OUTPUT_DIR = "fake_data/devis"
NUM_DEVIS = 10

TVA_RATE = 0.20
CURRENCY = "€"

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

# Génération du numéro de devis en utilisant la date actuelle
def generate_devis_number(index: int) -> str:
    year = date.today().year
    return f"DEV-{year}-{index:04d}"

# Génération des items dans le tableau
def generate_line_items() -> list[dict]:
    n = random.randint(2, 6)
    items = []
    # pour chaque items n on va attribuer info randoms
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

# Génération des données du devis qui appel generate_line_items() et generate_devis_number()
def generate_devis_data(index: int) -> dict:
    issue_date = fake.date_between(start_date="-90d", end_date="today")
    validity_days = random.choice([15, 30, 45, 60])
    validity_date = issue_date + timedelta(days=validity_days)

    items = generate_line_items()
    total_ht = round(sum(i["total_ht"] for i in items), 2)  #Total HT de TOUS les éléments
    tva = round(total_ht * TVA_RATE, 2)
    total_ttc = round(total_ht + tva, 2)

    return {
        "number": generate_devis_number(index),
        "issue_date": issue_date.strftime("%d/%m/%Y"),
        "validity_date": validity_date.strftime("%d/%m/%Y"),
        "seller": {
            "company": fake.company(),
            "address": fake.address().replace("\n", ", "),
            "email": fake.company_email(),
            "phone": fake.phone_number(),
            "siret": fake.siret(),
            "tva_intra": f"FR{random.randint(10, 99)}{fake.siret()[:9].replace(' ', '')}",
        },
        "client": {
            "company": fake.company(),
            "contact": fake.name(),
            "address": fake.address().replace("\n", ", "),
            "email": fake.email(),
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
        "title", fontSize=18, fontName="Helvetica-Bold", spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "subtitle", fontSize=9, fontName="Helvetica", textColor=colors.grey
    )
    section_style = ParagraphStyle(
        "section", fontSize=10, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=8
    )
    body_style = ParagraphStyle("body", fontSize=9, fontName="Helvetica", leading=13)

    primary = colors.HexColor("#1a73e8")
    light_bg = colors.HexColor("#f1f3f4")

    # On déclare le flux (story), c'est ça qui contiendra les éléments pour construire le pdf
    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    header_data = [
        [
            Paragraph(f"<b>{data['seller']['company']}</b>", title_style),
            Paragraph(
                f"<b>DEVIS N° {data['number']}</b>",
                ParagraphStyle("devnum", fontSize=16, fontName="Helvetica-Bold",
                               alignment=2, textColor=primary),
            ),
        ],
        [
            Paragraph(data["seller"]["address"], body_style),
            Paragraph(
                f"Date : {data['issue_date']}<br/>Valable jusqu'au : {data['validity_date']}",
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
    # header en tableau avec deux cols pour afficher
    header_table = Table(header_data, colWidths=[95 * mm, 75 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 2), (-1, 2), 0.5, colors.lightgrey),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8 * mm))

    # ── Client ──────────────────────────────────────────────────────────────
    story.append(Paragraph("ADRESSÉ À", section_style))
    client = data["client"]
    story.append(Paragraph(
        f"<b>{client['company']}</b><br/>"
        f"À l'attention de : {client['contact']}<br/>"
        f"{client['address']}<br/>"
        f"{client['email']}",
        body_style,
    ))
    story.append(Spacer(1, 8 * mm))

    # ── Objet du tableau d'élément───────────────────────────────────────────────────────────
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

    # ── Totals ───────────────────────────────────────────────────────────────
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
    story.append(Spacer(1, 12 * mm))

    # ── Bloc signature ────────────────────────────────────────────────────────
    story.append(Paragraph("ACCEPTATION DU DEVIS", section_style))
    sign_data = [
        [
            Paragraph(
                "Bon pour accord — Date : _______________<br/><br/><br/>"
                "Signature et cachet du client :",
                ParagraphStyle("sign_label", fontSize=9, fontName="Helvetica"),
            ),
            Paragraph(
                f"Fait à _______________<br/>Le {data['issue_date']}<br/><br/><br/>"
                "Signature du prestataire :",
                ParagraphStyle("sign_label2", fontSize=9, fontName="Helvetica"),
            ),
        ],
    ]
    sign_table = Table(sign_data, colWidths=[85 * mm, 85 * mm])
    sign_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (0, 0), 0.5, colors.lightgrey),
        ("BOX", (1, 0), (1, 0), 0.5, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sign_table)
    story.append(Spacer(1, 6 * mm))

    # ── Footer note ──────────────────────────────────────────────────────────
    story.append(Paragraph(
        "Ce devis est valable jusqu'à la date indiquée. Toute commande implique "
        "l'acceptation des présentes conditions. TVA non applicable si micro-entreprise "
        "(art. 293 B du CGI), sinon TVA au taux en vigueur.",
        ParagraphStyle("note", fontSize=8, fontName="Helvetica-Oblique",
                       textColor=colors.grey),
    ))

    doc.build(story)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for i in range(1, NUM_DEVIS + 1):
        data = generate_devis_data(i)
        filepath = os.path.join(OUTPUT_DIR, f"{data['number']}.pdf")
        build_pdf(data, filepath)
        print(f"[{i:02d}/{NUM_DEVIS}] Généré : {filepath}")
    print(f"\n✓ {NUM_DEVIS} devis créés dans le dossier « {OUTPUT_DIR}/»")


if __name__ == "__main__":
    main()
