# Data - Réupération de l'API et Génération de Datasets

## 📂 Structure du dossier

```text
data/
├── data_sirene/            # Zones de stockage (Architecture Médaillon)
│   ├── raw_data/           # Zone Bronze : JSON bruts de l'API
│   └── formatted_data/     # Zone Silver : Parquets et Jsons nettoyés
├── fake_data/              # Datasets générés (Factures, KBIS, RIB, URSSAF)
├── src/
│   ├── sirene/             # Scripts du pipeline ETL
│   │   ├── request_and_save_raw.py  # Extraction API 
│   │   ├── format_raw.py            # Transformation 
│   │   └── save_base.py             # Chargement MongoDB 
│   └── generate_file/      # Scripts de génération de PDF
├── utils.py                # Fonctions utilitaires partagées
├── run_sirene.py           # Orchestrateur du pipeline SIRENE
└── generate_all.py         # Orchestrateur de génération de documents
```

## 🚀 1. Pipeline SIRENE (Données Réelles)

Le pipeline suit une architecture **Médaillon** pour garantir la qualité des données.

* **Extraction ** : Le script `request_and_save_raw.py` interroge l'API SIRENE
de l'INSEE et stocke la réponse brute en JSON.
* **Transformation ** : Le script `format_raw.py` extrait les champs essentiels 
(SIRET, Adresse, Dirigeants), nettoie les formats et sauvegarde le résultat en **Parquet** 
* pour l'efficacité analytique.
* **Chargement (MongoDB)** : Le script `save_base.py` importe les fichiers Parquet dans 
MongoDB. Il enrichit les données en générant des informations de contact (email, téléphone)
* et des métadonnées de gestion.

**Commande pour lancer le pipeline :**
```bash
python run_sirene.py
```

## 📄 2. Génération de Datasets (Données de Test)

Pour tester la robustesse de l'IA, nous générons des documents PDF à partir des données
présentes en base de données.

### Types de documents générés :
* **Factures & Devis** : Générés avec `reportlab`, incluant des lignes 
de prestations aléatoires et des calculs de TVA.
* **Extraits KBIS** : Reconstitution fidèle d'un extrait d'immatriculation au RCS.
* **RIB** : Relevés d'identité bancaire avec calcul de clé RIB et IBAN valide.
* **Attestations URSSAF** : Attestations de vigilance avec QR Code de sécurité.

### Modes de génération :
* **Réaliste** : Utilise les entreprises existantes dans MongoDB pour créer des documents cohérents.
* **Incohérent (`--inconsistent`)** : Introduit volontairement des erreurs (SIREN erroné, adresse divergente, capital social modifié) pour tester les algorithmes de détection de fraude.
* **Aléatoire (`--random`)** : Utilise uniquement la bibliothèque `Faker` sans dépendance à MongoDB.

**Commande pour générer un dataset complet :**
```bash
python generate_all.py --random 
```

## 🛠 Installation

1.  **Dépendances** : Installez les bibliothèques nécessaires :
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configuration** : Créez un fichier `.env` à la racine avec vos accès :
    ```env
    API_SIRENE_TOKEN=votre_token_insee
    MONGODB_URI=mongodb://localhost:27017
    DB_NAME=hackathon
    ```

## 📊 Statistiques de sortie
Chaque exécution du pipeline ou du générateur produit des logs détaillés sur le nombre de lignes traitées, 
les succès d'insertion en base de données et les chemins des fichiers PDF créés.