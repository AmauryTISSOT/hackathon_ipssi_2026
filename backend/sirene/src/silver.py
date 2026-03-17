import os
from datetime import datetime
from pathlib import Path

import pandas as pd

def get_project_root():
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / ".env").exists():
            return parent
    return current_path.parent

ROOT_DIR = get_project_root()

BASE_PATH = os.path.join(ROOT_DIR, "data", "data_lake")
DIR_NAME = "api_sirene"
BRONZE_PATH = os.path.join(BASE_PATH, "bronze", DIR_NAME)
SILVER_PATH = os.path.join(BASE_PATH, "silver", DIR_NAME)


def safe(x):
    return x if x is not None else ""

def extract_essential_fields(raw_data):
    etablissements = raw_data.get('etablissements', [])
    records = []

    for etab in etablissements:
        unite = etab.get("uniteLegale", {})
        adresse = etab.get("adresseEtablissement", {})
        adresse_complete = ((f"{safe(adresse.get('numeroVoieEtablissement', ''))}"
                             f"{safe(adresse.get('indiceRepetitionEtablissement', ''))}"
                            f" {safe(adresse.get('typeVoieEtablissement', ''))} "
                            f"{safe(adresse.get('libelleVoieEtablissement', ''))}, "
                            f"{safe(adresse.get('codePostalEtablissement', ''))} "
                            f"{safe(adresse.get('libelleCommuneEtablissement', ''))}"
                             f" FRANCE"
                             f"{safe(adresse.get(' : complementAdresseEtablissement', ''))}"
                             )
                            .strip())
        clean_data = {
            "siren": etab.get("siren"),
            "nic": etab.get("nic"),
            "siret": etab.get("siret"),
            "dateCreationEtablissement": etab.get("dateCreationEtablissement"),
            "etablissementSiege": etab.get("etablissementSiege"),
            # Infos sur la marque
            "etatAdministratifUniteLegale": unite.get("etatAdministratifUniteLegale"),
            "dateCreationUniteLegale": unite.get("dateCreationUniteLegale"),
            "denominationUniteLegale": unite.get("denominationUniteLegale"),
            "activitePrincipaleUniteLegale": unite.get("activitePrincipaleUniteLegale"),
            "nomenclatureActivitePrincipaleUniteLegale": unite.get("nomenclatureActivitePrincipaleUniteLegale"),
            "categorieEntreprise": unite.get("categorieEntreprise"),
            # Adresse
            "adresseEtablissement": adresse_complete,
            "complementAdresseEtablissement": adresse.get("complementAdresseEtablissement"),
            "numeroVoieEtablissement": adresse.get("numeroVoieEtablissement"),
            "indiceRepetitionEtablissement": adresse.get("indiceRepetitionEtablissement"),
            "typeVoieEtablissement": adresse.get("typeVoieEtablissement"),
            "libelleVoieEtablissement": adresse.get("libelleVoieEtablissement"),
            "codePostalEtablissement": adresse.get("codePostalEtablissement"),
            "libelleCommuneEtablissement": adresse.get("libelleCommuneEtablissement"),
            "metadata": {"pipeline_processing_date": datetime.now().isoformat()}
        }
        records.append(clean_data)
    return pd.DataFrame(records)


def save_to_silver(df):
    os.makedirs(SILVER_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path_parquet = os.path.join(SILVER_PATH, f"sirene_full_{timestamp}.parquet")
    file_path_json = os.path.join(SILVER_PATH, f"sirene_full_{timestamp}.json")
    df.to_parquet(file_path_parquet, index=False)
    df.to_json(file_path_json, orient='records', force_ascii=False, indent=4)
    print(f"Fichiers Silver créés :\n - {file_path_parquet}\n - {file_path_json}")
    return file_path_parquet, file_path_json