from src.sirene.request_and_save_raw import fetch_sirene_data, save_to_bronze
from src.sirene.format_raw import extract_essential_fields, save_to_silver
def main():
    print("=== Démarrage du test du Pipeline SIRENE ===")

    try:
        print(f"\n[1/4] Appel de l'API Sirene...")
        raw_data = fetch_sirene_data(number=50)

        print("[2/4] Sauvegarde des données brutes en zone Bronze...")
        path_bronze = save_to_bronze(raw_data)
        print(f" -> Succès : Fichier créé dans {path_bronze}")

        print("\n[3/4] Extraction des champs essentiels et nettoyage...")
        df_silver = extract_essential_fields(raw_data)

        print(f" -> Nombre d'établissements traités : {len(df_silver)}")
        print(f" -> Colonnes générées : {list(df_silver.columns[:5])}...")

        print("[4/4] Sauvegarde en zone Silver (Format Parquet)...")
        path_silver = save_to_silver(df_silver)
        print(f" -> Succès : Fichier créé dans {path_silver}")

    except Exception as e:
        print(f"\n[ERREUR] Le pipeline a échoué : {e}")


if __name__ == "__main__":
    main()