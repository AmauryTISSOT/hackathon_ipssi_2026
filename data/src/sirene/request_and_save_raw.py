import os
import json
from pathlib import Path

import requests
from datetime import datetime
from dotenv import load_dotenv

from utils import get_project_root

ROOT_DIR = get_project_root()

load_dotenv(os.path.join(ROOT_DIR,".env"))
BASE_PATH = os.path.join(ROOT_DIR, "data", "data_sirene")
BRONZE_PATH = os.path.join(BASE_PATH, "raw_data")


def get_api_token():
    return os.getenv("API_SIRENE_TOKEN")

def fetch_sirene_data(number=100):
    token = get_api_token()
    url = f"https://api.insee.fr/api-sirene/3.11/siret?nombre={number}"
    headers = {"X-INSEE-Api-Key-Integration": f"{token}", "Accept": "application/json;charset=utf-8;qs=1"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def save_to_bronze(data):
    os.makedirs(BRONZE_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(BRONZE_PATH, f"sirene_raw_{timestamp}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return file_path