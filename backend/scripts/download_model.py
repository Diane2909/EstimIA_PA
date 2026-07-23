"""
EstimIA — Récupération des artefacts ML au démarrage du conteneur backend.

Les fichiers .pkl (modèle + colonnes + lookup géographique) ne sont pas
versionnés dans git (trop volumineux, cf. .gitignore). Le projet peut être
déployé sur AWS ou sur Azure (voir docs/aws-setup.md et docs/azure-setup.md) ;
ce script détecte automatiquement lequel des deux jeux de variables
d'environnement est renseigné et télécharge les fichiers en conséquence,
avant que backend/entrypoint.sh ne lance uvicorn.

Si le dossier backend/model contient déjà les 3 fichiers (ex: volume monté
en local avec docker-compose), le téléchargement est simplement ignoré.
"""

import os
import sys
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
FILENAMES = [
    "modele_estimation.pkl",
    "colonnes_modele.pkl",
    "lookup_postaux.pkl",
]


def download_from_s3() -> int:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    bucket = os.environ["AWS_S3_BUCKET"]
    region = os.environ.get("AWS_REGION", "eu-west-3")
    prefix = os.environ.get("AWS_S3_MODEL_PREFIX", "")

    s3 = boto3.client("s3", region_name=region)

    for filename in FILENAMES:
        dest = MODEL_DIR / filename
        key = f"{prefix}{filename}" if prefix else filename
        print(f"[INFO] Téléchargement de {filename} depuis s3://{bucket}/{key}...")
        try:
            s3.download_file(bucket, key, str(dest))
            print(f"[SUCCESS] {filename} téléchargé ({dest.stat().st_size / 1e6:.1f} Mo).")
        except (BotoCoreError, ClientError) as e:
            print(f"[ERROR] Échec du téléchargement de {filename} : {e}")
            return 1
    return 0


def download_from_azure() -> int:
    import requests

    account_url = os.environ["AZURE_STORAGE_ACCOUNT_URL"].rstrip("/")
    container = os.environ.get("AZURE_STORAGE_CONTAINER", "models")
    sas_token = os.environ["AZURE_STORAGE_SAS_TOKEN"]
    sas_query = sas_token if sas_token.startswith("?") else f"?{sas_token}"

    for filename in FILENAMES:
        dest = MODEL_DIR / filename
        url = f"{account_url}/{container}/{filename}{sas_query}"
        print(f"[INFO] Téléchargement de {filename} depuis Azure Blob Storage...")
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            print(f"[SUCCESS] {filename} téléchargé ({len(resp.content) / 1e6:.1f} Mo).")
        except requests.RequestException as e:
            print(f"[ERROR] Échec du téléchargement de {filename} : {e}")
            return 1
    return 0


def main() -> int:
    MODEL_DIR.mkdir(exist_ok=True)

    if all((MODEL_DIR / f).exists() for f in FILENAMES):
        print("[INFO] Artefacts ML déjà présents localement, téléchargement ignoré.")
        return 0

    if os.environ.get("AWS_S3_BUCKET"):
        return download_from_s3()

    if os.environ.get("AZURE_STORAGE_ACCOUNT_URL") and os.environ.get("AZURE_STORAGE_SAS_TOKEN"):
        return download_from_azure()

    print(
        "[WARNING] Ni AWS_S3_BUCKET ni AZURE_STORAGE_ACCOUNT_URL/AZURE_STORAGE_SAS_TOKEN "
        "ne sont définis : démarrage sans modèle ML (l'API répondra en mode dégradé)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
