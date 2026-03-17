# Hackathon IPSSI 2026 — Plateforme IA de traitement de documents administratifs

## Etudiants

- Damien LORTIE THIBAUT
- Pierre GUITARD
- William HOANG
- Seer MENSAH ASSIAKOLEY
- Sedanur OZDEMIR
- Evan AFONSO
- Amaury TISSOT

## Prérequis

- Docker & Docker Compose
- Un compte Azure (Azure for Students suffit)

## Configuration Azure Document Intelligence

### 1. Créer la ressource sur Azure

1. Se connecter sur [portal.azure.com](https://portal.azure.com)
2. Cliquer **"Créer une ressource"**
3. Rechercher **"Document Intelligence"**
4. Cliquer **Créer** et remplir :
    - **Abonnement** : Azure for Students
    - **Groupe de ressources** : créer un nouveau (ex: `hackathon-rg`)
    - **Région** : choisir parmi les régions autorisées :
        - `UK South`
        - `Germany West Central`
        - `Switzerland North` (recommandé)
        - `Spain Central`
        - `Italy North`
    - **Nom** : un nom unique (ex: `hackathon-doc-intel-2026`)
    - **Niveau tarifaire** : **F0 (gratuit)** — 500 pages/mois
5. Cliquer **Vérifier + Créer** puis **Créer**

### 2. Récupérer les credentials

1. Une fois déployé, cliquer **"Accéder à la ressource"**
2. Dans le menu de gauche, aller dans **"Clés et point de terminaison"**
3. Copier :
    - **Point de terminaison** → `AZURE_DI_ENDPOINT`
    - **CLÉ 1** → `AZURE_DI_KEY`

### 3. Configurer le `.env`

Copier le fichier d'environnement d'exemple et remplir les credentials Azure :

```bash
cp .env.example .env
```

Puis éditer le `.env` :

```env
AZURE_DI_ENDPOINT=https://<url-resource>.cognitiveservices.azure.com/
AZURE_DI_KEY=<clé-api>
```

## Lancement

```bash
docker compose up -d
```
