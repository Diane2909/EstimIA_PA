import re
import sys
import unicodedata
from pathlib import Path
import pandas as pd
import joblib


def normaliser_nom(nom: str) -> str:
    """Normalise un nom de commune pour la comparaison : minuscules, sans accents,
    tirets/apostrophes remplacés par des espaces, espaces multiples réduits."""
    nom = str(nom).strip().lower()
    nom = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode("ascii")
    nom = re.sub(r"[-'’]", " ", nom)
    nom = re.sub(r"\s+", " ", nom).strip()
    return nom


def main():
    print("===========================================================")
    print("GENERATION DE LA TABLE DE CORRESPONDANCE GEOGRAPHIQUE")
    print("===========================================================")

    # Resolution des chemins
    script_dir = Path(__file__).resolve().parent
    csv_path = script_dir / "processed" / "dataset_propre.csv"
    if not csv_path.exists():
        csv_path = Path("backend/data/processed/dataset_propre.csv")
    if not csv_path.exists():
        csv_path = Path("data/processed/dataset_propre.csv")

    if not csv_path.exists():
        print(f"[ERROR] Impossible de trouver le dataset propre : {csv_path}")
        sys.exit(1)

    print(f"Chargement des donnees depuis : {csv_path.resolve()}")
    df = pd.read_csv(
        csv_path,
        dtype={'code_postal': str, 'code_insee': str, 'departement': str},
        low_memory=False
    )
    print(f"Dataset charge : {len(df):,} lignes.")

    # Nettoyage et uniformisation du code postal
    df = df.dropna(subset=['code_postal', 'latitude', 'longitude'])
    df['code_postal'] = df['code_postal'].astype(str).str.replace(r'\.0$', '', regex=True)
    df['code_postal'] = df['code_postal'].apply(lambda x: x.zfill(5) if x not in ['nan', 'None', ''] else '')
    df = df[df['code_postal'] != '']

    # Ajouter le code departement a partir du code postal (2 premiers caracteres)
    df['departement_extracted'] = df['code_postal'].str[:2]

    print("Calcul des medianes par Code Postal...")
    # Regrouper par code postal pour calculer les medianes
    grouped_postal = df.groupby('code_postal').agg({
        'latitude': 'median',
        'longitude': 'median',
        'score_dpe_median': 'median',
        'score_georisques': 'median',
        'score_delinquance': 'median',
        'departement_extracted': 'first'
    }).reset_index()

    lookup_postaux = {}
    for _, row in grouped_postal.iterrows():
        lookup_postaux[row['code_postal']] = {
            'latitude': float(row['latitude']),
            'longitude': float(row['longitude']),
            'score_dpe_median': float(row['score_dpe_median']),
            'score_georisques': float(row['score_georisques']),
            'score_delinquance': float(row['score_delinquance']),
            'departement': str(row['departement_extracted'])
        }

    print("Calcul des medianes par Departement...")
    # Regrouper par departement pour le fallback de securite
    grouped_dept = df.groupby('departement_extracted').agg({
        'latitude': 'median',
        'longitude': 'median',
        'score_dpe_median': 'median',
        'score_georisques': 'median',
        'score_delinquance': 'median'
    }).reset_index()

    lookup_depts = {}
    for _, row in grouped_dept.iterrows():
        lookup_depts[row['departement_extracted']] = {
            'latitude': float(row['latitude']),
            'longitude': float(row['longitude']),
            'score_dpe_median': float(row['score_dpe_median']),
            'score_georisques': float(row['score_georisques']),
            'score_delinquance': float(row['score_delinquance'])
        }

    print("Construction de la table Nom de commune -> Code postal...")
    lookup_communes = {}
    if 'nom_commune' in df.columns:
        df['nom_commune_norm'] = df['nom_commune'].apply(normaliser_nom)
        # Pour chaque commune, on retient le code postal le plus fréquent dans les transactions
        communes_map = (
            df.groupby('nom_commune_norm')['code_postal']
            .agg(lambda s: s.value_counts().idxmax())
        )
        lookup_communes = communes_map.to_dict()
    else:
        print("[WARNING] Colonne 'nom_commune' absente — table de noms de commune non generee.")

    lookup_table = {
        'postaux': lookup_postaux,
        'departements': lookup_depts,
        'communes': lookup_communes,
    }

    # Sauvegarde de la table
    model_dir = script_dir.parent / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    output_path = model_dir / "lookup_postaux.pkl"

    joblib.dump(lookup_table, output_path)
    print(f"[SUCCESS] Table de correspondance generee avec succes !")
    print(f"  Nombre de codes postaux enregistres : {len(lookup_postaux)}")
    print(f"  Nombre de departements enregistres  : {len(lookup_depts)}")
    print(f"  Nombre de communes enregistrees     : {len(lookup_communes)}")
    print(f"  Fichier enregistre sous : {output_path.resolve()}")

if __name__ == "__main__":
    main()
