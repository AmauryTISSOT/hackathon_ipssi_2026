import re
from datetime import datetime


def validate_iban(iban):
    """
    Valide un IBAN selon l'algorithme modulo 97.
    
    Étapes:
    1. Prendre les 4 premiers caractères et les mettre à la fin
    2. Convertir les lettres en nombres (A=10, B=11, ..., Z=35)
    3. Calculer modulo 97, le reste doit être 1
    
    Exemple: FR7630006000011234567890189
    - Réarrangement: 30006000011234567890189FR76
    - Conversion: 30006000011234567890189152776
    - Modulo 97: 1 ✓
    """
    if not iban or not isinstance(iban, str):
        return False, "IBAN vide ou invalide"
    
    cleaned = iban.replace(" ", "").upper()
    
    if len(cleaned) < 15 or len(cleaned) > 34:
        return False, f"Longueur IBAN incorrecte ({len(cleaned)} caractères)"
    
    rearranged = cleaned[4:] + cleaned[:4]
    
    numeric = ""
    for char in rearranged:
        if char.isalpha():
            numeric += str(ord(char) - 55)
        else:
            numeric += char
    
    remainder = 0
    for digit in numeric:
        remainder = (remainder * 10 + int(digit)) % 97
    
    if remainder == 1:
        return True, "IBAN valide"
    else:
        return False, f"IBAN invalide: modulo 97 = {remainder} (attendu: 1)"


def validate_tva_number(tva_number, country_code=None):
    """
    Valide la structure d'un numéro de TVA selon le pays.
    
    Formats supportés:
    - France (FR): FR + 2 chiffres (clé) + 9 chiffres (SIREN)
    - Belgique (BE): BE + 10 chiffres
    - Allemagne (DE): DE + 9 chiffres
    - Espagne (ES): ES + 9 caractères (lettre ou chiffre)
    - Italie (IT): IT + 11 chiffres
    """
    if not tva_number or not isinstance(tva_number, str):
        return False, "Numéro de TVA vide ou invalide"
    
    cleaned = tva_number.replace(" ", "").replace(".", "").upper()
    
    patterns = {
        "FR": (r"^FR[0-9A-Z]{2}[0-9]{9}$", "FR + 2 caractères + 9 chiffres"),
        "BE": (r"^BE[0-9]{10}$", "BE + 10 chiffres"),
        "DE": (r"^DE[0-9]{9}$", "DE + 9 chiffres"),
        "ES": (r"^ES[0-9A-Z][0-9]{7}[0-9A-Z]$", "ES + 9 caractères"),
        "IT": (r"^IT[0-9]{11}$", "IT + 11 chiffres"),
        "LU": (r"^LU[0-9]{8}$", "LU + 8 chiffres"),
        "NL": (r"^NL[0-9]{9}B[0-9]{2}$", "NL + 9 chiffres + B + 2 chiffres"),
        "PT": (r"^PT[0-9]{9}$", "PT + 9 chiffres"),
    }
    
    if len(cleaned) < 2:
        return False, "Numéro de TVA trop court"
    
    detected_country = cleaned[:2]
    
    if country_code and detected_country != country_code:
        return False, f"Code pays {detected_country} ne correspond pas au pays attendu {country_code}"
    
    if detected_country not in patterns:
        return False, f"Format de TVA non reconnu pour le pays {detected_country}"
    
    pattern, format_desc = patterns[detected_country]
    
    if not re.match(pattern, cleaned):
        return False, f"Format invalide pour {detected_country}. Attendu: {format_desc}"
    
    return True, f"Numéro de TVA {detected_country} valide"


def validate_invoice_dates(issue_date, due_date):
    """
    Valide que la date d'échéance est postérieure à la date d'émission.
    
    Args:
        issue_date: Date d'émission (str au format DD/MM/YYYY ou objet datetime)
        due_date: Date d'échéance (str au format DD/MM/YYYY ou objet datetime)
    
    Returns:
        (bool, str): (validité, message)
    """
    if not issue_date or not due_date:
        return True, "Dates manquantes, validation ignorée"
    
    try:
        if isinstance(issue_date, str):
            issue_dt = datetime.strptime(issue_date, "%d/%m/%Y")
        else:
            issue_dt = issue_date
        
        if isinstance(due_date, str):
            due_dt = datetime.strptime(due_date, "%d/%m/%Y")
        else:
            due_dt = due_date
        
        if due_dt < issue_dt:
            return False, f"Date d'échéance ({due_date}) antérieure à la date d'émission ({issue_date})"
        
        return True, "Dates cohérentes"
    
    except ValueError as e:
        return False, f"Format de date invalide: {str(e)}"


def perform_controls(**context):
    """
    Tâche Airflow qui effectue tous les contrôles de conformité sur les données gold.
    
    Cette tâche se situe entre validate_and_store_gold et save_to_mongodb.
    Elle ajoute des alertes supplémentaires basées sur les contrôles métier.
    """
    gold_data = context["ti"].xcom_pull(task_ids="validate_and_store_gold")
    
    if not gold_data:
        raise ValueError("Aucune donnée gold reçue")
    
    entities = gold_data.get("entities", {})
    alerts = gold_data.get("validation", {}).get("alerts", [])
    doc_type = entities.get("doc_type")
    
    print(f"[CONTROLS] Début des contrôles pour document de type: {doc_type}")
    
    # Contrôle 1: Validation IBAN (pour RIB et factures avec IBAN)
    iban = entities.get("iban")
    iban_valid = False
    if iban:
        iban_valid, iban_message = validate_iban(iban)
        print(f"[CONTROLS] IBAN: {iban_message}")
        if not iban_valid:
            alerts.append({
                "type": "iban_invalid",
                "message": iban_message,
                "severity": "error",
                "control": "iban_validation"
            })
    
    # Contrôle 2: Validation du numéro de TVA intracommunautaire
    tva_number = entities.get("tva_number") or entities.get("vendor_tax_id")
    tva_number_valid = False
    if tva_number:
        tva_number_valid, tva_message = validate_tva_number(tva_number)
        print(f"[CONTROLS] Numéro TVA: {tva_message}")
        if not tva_number_valid:
            alerts.append({
                "type": "tva_number_invalid",
                "message": tva_message,
                "severity": "warning",
                "control": "tva_number_validation"
            })
    
    # Contrôle 3: Validation des dates (factures uniquement)
    if doc_type == "facture":
        issue_date = entities.get("issue_date") or entities.get("date_document")
        due_date = entities.get("due_date") or entities.get("date_echeance")
        
        if issue_date and due_date:
            dates_valid, dates_message = validate_invoice_dates(issue_date, due_date)
            print(f"[CONTROLS] Dates facture: {dates_message}")
            if not dates_valid:
                alerts.append({
                    "type": "invoice_dates_invalid",
                    "message": dates_message,
                    "severity": "error",
                    "control": "invoice_dates_validation"
                })
    
    # Mise à jour des données gold avec les nouveaux contrôles
    gold_data["validation"]["alerts"] = alerts
    gold_data["validation"]["iban_valid"] = iban_valid
    gold_data["validation"]["tva_number_valid"] = tva_number_valid
    gold_data["validation"]["controls_performed"] = True
    
    control_count = len([a for a in alerts if a.get("control")])
    error_count = len([a for a in alerts if a.get("severity") == "error"])
    warning_count = len([a for a in alerts if a.get("severity") == "warning"])
    
    print(f"[CONTROLS] Contrôles terminés: {control_count} contrôles, {error_count} erreurs, {warning_count} avertissements")
    
    return gold_data
