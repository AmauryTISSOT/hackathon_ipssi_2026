import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from data.utils import get_project_root, safe

ROOT_DIR = get_project_root()

BASE_PATH = os.path.join(ROOT_DIR, "data", "data_sirene")
BRONZE_PATH = os.path.join(BASE_PATH, "raw_data")
SILVER_PATH = os.path.join(BASE_PATH, "formatted_data")



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
        periodes = etab.get("periodesEtablissement", [])
        enseigne = periodes[0].get("enseigne1Etablissement") if periodes else None
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
            "categorieJuridiqueUniteLegale": unite.get("categorieJuridiqueUniteLegale"),
            "activitePrincipaleUniteLegale": unite.get("activitePrincipaleUniteLegale"),
            "nomenclatureActivitePrincipaleUniteLegale": unite.get("nomenclatureActivitePrincipaleUniteLegale"),
            "categorieEntreprise": unite.get("categorieEntreprise"),
            "enseigneEtablissement": enseigne,
            "sexeUniteLegale": unite.get("sexeUniteLegale"),
            "nomUniteLegale": unite.get("nomUniteLegale"),
            "nomUsageUniteLegale": unite.get("nomUsageUniteLegale"),
            "prenom1UniteLegale": unite.get("prenom1UniteLegale"),
            "prenomUsuelUniteLegale": unite.get("prenomUsuelUniteLegale"),
            # Adresse
            "adresseEtablissement": adresse_complete,
            "complementAdresseEtablissement": adresse.get("complementAdresseEtablissement"),
            "numeroVoieEtablissement": adresse.get("numeroVoieEtablissement"),
            "indiceRepetitionEtablissement": adresse.get("indiceRepetitionEtablissement"),
            "typeVoieEtablissement": adresse.get("typeVoieEtablissement"),
            "libelleVoieEtablissement": adresse.get("libelleVoieEtablissement"),
            "codePostalEtablissement": adresse.get("codePostalEtablissement"),
            "libelleCommuneEtablissement": adresse.get("libelleCommuneEtablissement"),
            "metadata": {"pipeline_processing_date": datetime.now().isoformat(), "source": "api_sirene_v3"}
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