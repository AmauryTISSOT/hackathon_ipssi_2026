import os
from pathlib import Path
import random

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import numpy as np
from faker import Faker

from data.utils import get_project_root, safe, clean_value, build_metadata, get_latest_parquet

ROOT_DIR = get_project_root()
load_dotenv(os.path.join(ROOT_DIR, ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "Hackathon")
COLLECTION_NAME = "Company"
DATA_DIR = Path(os.path.join(ROOT_DIR, "data", "data_sirene", "formatted_data"))

fake = Faker('fr_FR')

def generate_mail(lastname, firstname, denomination, enseigne):
    if denomination:
        domain_name = denomination.lower()
        domain_name = domain_name.replace(" ", "").replace("-", "").replace("'", "").replace(".", "")
        domain_name = (domain_name.replace("é", "e").replace("è", "e").replace("ê", "e")
                       .replace("à", "a").replace("â", "a")
                       .replace("î", "i").replace("ï", "i")
                       .replace("ô", "o").replace("ö", "o")
                       .replace("û", "u").replace("ü", "u")
                       .replace("ç", "c"))
        domain_name = ''.join(c for c in domain_name if c.isalnum())
        if domain_name:
            domain = f"{domain_name}.fr"
        else:
            domain = fake.domain_name()
    elif enseigne:
        domain_name = enseigne.lower()
        domain_name = domain_name.replace(" ", "").replace("-", "").replace("'", "").replace(".", "")
        domain_name = (domain_name.replace("é", "e").replace("è", "e").replace("ê", "e")
                       .replace("à", "a").replace("â", "a")
                       .replace("î", "i").replace("ï", "i")
                       .replace("ô", "o").replace("ö", "o")
                       .replace("û", "u").replace("ü", "u")
                       .replace("ç", "c"))
        domain_name = ''.join(c for c in domain_name if c.isalnum())
        if domain_name:
            domain = f"{domain_name}.fr"
        else:
            domain = fake.domain_name()
    else:
        domain = fake.domain_name()

    email = f"{firstname.lower()}.{lastname.lower()}@{domain}"
    return clean_value(email.replace(' ', '.').replace("'", ""))

def generate_manager_info(company_data):
    categorie_juridique = safe(company_data.get('categorie_juridique_unite_legale', ''))
    sexe = safe(company_data.get('sexe_unite_legale', 'Pas spécifié'))
    denomination = clean_value(safe(company_data.get('denomination_unite_legale', '')))
    enseigne = clean_value(safe(company_data.get('enseigne_etablissement', '')))
    if sexe == 'M':
        fake_gender = 'male'
    elif sexe == 'F':
        fake_gender = 'female'
    else:
        fake_gender = random.choice(['male', 'female'])
    if fake_gender == 'male':
        prenom = fake.first_name_male()
    else:
        prenom = fake.first_name_female()
    if categorie_juridique == '1000':
        nom = clean_value(safe(company_data.get('nom_unite_legale')))
        prenom_existant = clean_value(safe(company_data.get('prenom_1_unite_legale')))
        prenom_usuel = clean_value(safe(company_data.get('prenom_usuel_unite_legale')))
        if nom:
            lastname = nom.upper()
        else:
            lastname = fake.last_name().upper()
        if prenom_existant:
            firstname = prenom_usuel if (prenom_usuel and prenom_usuel != prenom_existant) else prenom_existant
        else:
            firstname = prenom
    else:
        lastname = fake.last_name().upper()
        firstname = prenom
    email = generate_mail(lastname, firstname, denomination, enseigne)
    birth_date = datetime.combine(fake.date_of_birth(minimum_age=25, maximum_age=65), datetime.min.time())
    return {
        "nom": clean_value(lastname),
        "prenom": clean_value(firstname),
        "email": email,
        "date_naissance": birth_date,
        "lieu_naissance": clean_value(fake.city()),
        "nationalite": "FRANCAISE",
        "fonction": clean_value(random.choice(['Président', 'Directeur Général', 'Gérant', 'Associé unique'])),
        "adresse": clean_value(safe(company_data.get('adresse_etablissement', fake.address().replace('\n', ', ')))),
        "sexe": 'M' if fake_gender == 'male' else 'F',
        "telephone": clean_value(fake.phone_number()),
        "role_comptable": random.choice([True, False])
    }

def clean_and_map_data(df):
    mapping = {
        'siren': 'siren',
        'nic': 'nic',
        'siret': 'siret',
        'dateCreationEtablissement': 'date_creation_etablissement',
        'etablissementSiege': 'etablissement_siege',
        'etatAdministratifUniteLegale': 'etat_administratif_unite_legale',
        'dateCreationUniteLegale': 'date_creation_unite_legale',
        'denominationUniteLegale': 'denomination_unite_legale',
        'categorieJuridiqueUniteLegale': 'categorie_juridique_unite_legale',
        'activitePrincipaleUniteLegale': 'activite_principale_unite_legale',
        'nomenclatureActivitePrincipaleUniteLegale': 'nomenclature_activite_principale_unite_legale',
        'categorieEntreprise': 'categorie_entreprise',
        'enseigneEtablissement': 'enseigne_etablissement',
        'sexeUniteLegale': 'sexe_unite_legale',
        'nomUniteLegale': 'nom_unite_legale',
        'nomUsageUniteLegale': 'nom_usage_unite_legale',
        'prenom1UniteLegale': 'prenom_1_unite_legale',
        'prenomUsuelUniteLegale': 'prenom_usuel_unite_legale',
        'adresseEtablissement': 'adresse_etablissement',
        'complementAdresseEtablissement': 'complement_adresse_etablissement',
        'numeroVoieEtablissement': 'numero_voie_etablissement',
        'indiceRepetitionEtablissement': 'indice_repetition_etablissement',
        'typeVoieEtablissement': 'type_voie_etablissement',
        'libelleVoieEtablissement': 'libelle_voie_etablissement',
        'codePostalEtablissement': 'code_postal_etablissement',
        'libelleCommuneEtablissement': 'libelle_commune_etablissement'
    }
    existing_columns = {old: new for old, new in mapping.items() if old in df.columns}
    df = df.rename(columns=existing_columns)
    expected_fields = [
        'siren', 'nic', 'siret', 'date_creation_etablissement', 'etablissement_siege',
        'etat_administratif_unite_legale', 'date_creation_unite_legale',
        'denomination_unite_legale', 'categorie_juridique_unite_legale',
        'activite_principale_unite_legale', 'nomenclature_activite_principale_unite_legale',
        'categorie_entreprise', 'enseigne_etablissement', 'sexe_unite_legale',
        'nom_unite_legale', 'nom_usage_unite_legale', 'prenom_1_unite_legale',
        'prenom_usuel_unite_legale', 'adresse_etablissement', 'complement_adresse_etablissement',
        'numero_voie_etablissement', 'indice_repetition_etablissement', 'type_voie_etablissement',
        'libelle_voie_etablissement', 'code_postal_etablissement', 'libelle_commune_etablissement'
    ]
    for field in expected_fields:
        if field not in df.columns:
            df[field] = None
    df['sexe_unite_legale'] = df['sexe_unite_legale'].apply(
        lambda x: x if x in ['M', 'F'] else 'Pas spécifié'
    )
    date_fields = ['date_creation_etablissement', 'date_creation_unite_legale']
    for field in date_fields:
        if field in df.columns:
            df[field] = pd.to_datetime(df[field], errors='coerce')
            df[field] = df[field].where(pd.notna(df[field]), None)
    if 'etablissement_siege' in df.columns:
        df['etablissement_siege'] = df['etablissement_siege'].astype(bool)
    text_fields = ['denomination_unite_legale', 'enseigne_etablissement', 'nom_unite_legale',
                   'nom_usage_unite_legale', 'prenom_1_unite_legale', 'prenom_usuel_unite_legale',
                   'adresse_etablissement', 'complement_adresse_etablissement', 'type_voie_etablissement',
                   'libelle_voie_etablissement', 'libelle_commune_etablissement']
    for field in text_fields:
        if field in df.columns:
            df[field] = df[field].apply(lambda x: clean_value(x) if pd.notna(x) else None)
    numeric_fields = ['numero_voie_etablissement', 'code_postal_etablissement']
    for field in numeric_fields:
        if field in df.columns:
            df[field] = df[field].apply(lambda x: str(x) if pd.notna(x) else None)
    df['metadata'] = df.apply(build_metadata, axis=1)
    df = df.replace({np.nan: None})
    final_columns = expected_fields + ['metadata']
    return df[final_columns]


def main():
    try:
        parquet_file = get_latest_parquet(DATA_DIR)
        if not parquet_file:
            print("Aucun fichier à traiter")
            return
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        company_collection = db[COLLECTION_NAME]
        print(f"Début de l'ingestion du fichier {os.path.basename(parquet_file)}")
        print("Chargement du fichier Parquet...")
        df_raw = pd.read_parquet(parquet_file)
        print(f"{len(df_raw)} lignes chargées")
        print("Transformation des données...")
        df_final = clean_and_map_data(df_raw)
        records = df_final.to_dict(orient='records')
        if records:
            print(f"Structure des données : {len(records[0])} champs par document")
            batch_size = 1000
            total_inserted = 0
            total_existing = 0
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                enriched_batch = []
                for company in batch:
                    siret = safe(company.get('siret'))
                    existing_company = company_collection.find_one({"siret": siret})
                    if existing_company:
                        total_existing += 1
                        continue
                    manager_info = generate_manager_info(company)
                    company['manager'] = {
                        "nom": manager_info['nom'],
                        "prenom": manager_info['prenom'],
                        "email": manager_info['email'],
                        "date_naissance": manager_info['date_naissance'],
                        "lieu_naissance": manager_info['lieu_naissance'],
                        "nationalite": manager_info['nationalite'],
                        "fonction": manager_info['fonction'],
                        "telephone": manager_info['telephone'],
                    }
                    enriched_batch.append(company)
                if enriched_batch:
                    try:
                        result = company_collection.insert_many(enriched_batch, ordered=False)
                        total_inserted += len(result.inserted_ids)
                        print(f"Lot {i // batch_size + 1} : {len(result.inserted_ids)} nouvelles entreprises insérées")
                    except Exception as e:
                        if "E11000" in str(e):
                            for company in enriched_batch:
                                try:
                                    company_collection.insert_one(company)
                                    total_inserted += 1
                                except Exception as insert_error:
                                    if "E11000" in str(insert_error):
                                        total_existing += 1
                                        print(f"Doublon ignoré pour le SIRET {company.get('siret')}")
                                    else:
                                        print(f"Erreur inattendue pour le SIRET {company.get('siret')}: {insert_error}")
                        else:
                            print(f"Erreur lors de l'insertion du lot: {e}")
                print(f"Statistiques partielles - Nouvelles: {total_inserted}, Existantes: {total_existing}")
            print(f"\nSuccès !")
            print(f"  - Nouvelles entreprises insérées : {total_inserted}")
            print(f"  - Entreprises déjà existantes (ignorées) : {total_existing}")
            print(f"  - Total traité : {total_inserted + total_existing}")
        else:
            print("Aucune donnée à insérer.")
    except Exception as e:
        print(f"Erreur lors de l'ingestion : {e}")
    finally:
        client.close()
        print("Connexion MongoDB fermée")

if __name__ == "__main__":
    main()