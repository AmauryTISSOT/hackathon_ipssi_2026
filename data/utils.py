from pathlib import Path

import pandas as pd


def get_project_root():
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / ".env").exists():
            return parent
    return current_path.parent


def safe(x):
    return x if x is not None else ""

def clean_value(x):
    if pd.isna(x) or x == '[ND]' or x == 'null' or x == '':
        return None
    return x

def get_latest_parquet(data_dir):
    try:
        parquet_files = list(data_dir.glob("*.parquet"))
        if not parquet_files:
            raise FileNotFoundError(f"Aucun fichier parquet trouvé dans {data_dir}")
        latest_file = max(parquet_files, key=lambda f: f.stat().st_mtime)
        print(f"Fichier trouvé : {latest_file}")
        return str(latest_file)
    except Exception as e:
        print(f"Erreur lors de la recherche du fichier : {e}")
        return None

def build_metadata(row):
    return row["metadata"]
