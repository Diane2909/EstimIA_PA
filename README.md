# EstimIA — L'estimation immobilière augmentée

> Application web terrain permettant aux agents immobiliers de produire un rapport d'estimation complet, précis et professionnel en moins de 5 minutes — directement sur le terrain.

---

## Présentation

EstimIA combine la précision du calcul statistique et l'intelligence d'un modèle de langage local (SLM) pour produire des estimations immobilières en temps réel. L'application interroge les données ouvertes françaises (DVF, DPE, Géorisques, Délinquance) et génère un rapport structuré sans jamais envoyer de données sensibles vers un cloud externe.

**Projet annuel — groupe de 2-3 personnes**

---

## Architecture réelle

```
Agent immobilier (saisit adresse + critères)
        │
        ▼
Frontend — Streamlit + Folium (carte interactive)
        │
        │  Appels Python directs
        ▼
Backend — Python FastAPI
        │
        ├──► Moteur ML (Scikit-learn)
        │       ├── Régression prix (RandomForest / KNN)
        │       └── Clustering biens (K-Means)
        │
        ├──► tools.py (outils de l'agent)
        │       ├── estimer_prix()
        │       └── obtenir_risques_climatiques()
        │
        └──► Agent IA (Ollama + LangChain)
                └── Modèle local Llama 3 GGUF — synthèse rapport

Sources de données (data.gouv.fr — open data officiel)
        ├── DVF (transactions foncières)
        ├── DPE (diagnostics énergétiques — ADEME)
        ├── Géorisques (API officielle)
        └── Délinquance (Interstats)

Déploiement
        └── Docker → AWS EC2
```

### Choix techniques justifiés

| Composant | Choix | Justification |
|-----------|-------|---------------|
| Frontend | Streamlit + streamlit-folium | Tout en Python, carte interactive, démo jury immédiate |
| Carte | Folium | Clic → latitude/longitude automatique |
| Backend | Python FastAPI | Async, compatible ML, léger |
| ML | Scikit-learn (RandomForest / KNN) | Adapté aux données spatiales, pas de GPU requis |
| LLM | Ollama (Llama 3 GGUF local) | Zéro coût API, RGPD natif, données non exposées |
| Orchestration | LangChain | Liaison LLM ↔ tools.py |
| Données | data.gouv.fr + API Géorisques | Open data officiel, gratuit |
| Déploiement | Docker + AWS EC2 | Scalable, Free Tier 12 mois |

---

## Stack technique

- **Frontend** : Streamlit, streamlit-folium, Folium
- **Backend** : Python 3.11+, FastAPI, Uvicorn
- **Machine Learning** : Scikit-learn, Pandas, NumPy, GeoPandas
- **Agent IA** : Ollama (Llama 3 GGUF), LangChain
- **Données** : DVF data.gouv.fr, DPE ADEME, API Géorisques, Délinquance Interstats
- **Infra** : Docker, AWS EC2, Ngrok (hybride si besoin)
- **Qualité code** : Ruff (linter + formatter)

---

## Features du modèle ML

Features utilisées pour la régression de prix :

| Feature | Source | Type |
|---------|--------|------|
| Surface (m²) | DVF | Numérique |
| Nombre de pièces | DVF | Numérique |
| Type de bien (appt/maison) | DVF | Catégoriel |
| Classe DPE (A→G encodée 1–7) | DPE ADEME | Ordinal |
| Score Géorisques (0–10) | Géorisques | Numérique |
| Score insécurité (0–10) | Interstats | Numérique |
| Code INSEE commune | DVF | Encodé |
| Médiane transactions DVF 500m | DVF | Numérique |

**Clustering K-Means** : les biens sont regroupés en 4–6 classes (ex : studio centre-ville, appartement familial périurbain, maison avec terrain) pour contextualiser l'estimation dans le rapport.

---

## Utilisation du LLM

Le LLM est utilisé **uniquement pour la synthèse narrative** du rapport. Il ne prédit pas de prix.

- Reçoit en entrée : prix estimé, intervalle de confiance, classe DPE, score risques, cluster du bien, transactions comparables
- Génère : un rapport en langage naturel structuré (résumé, analyse, points forts/faibles, recommandations)
- Pas de fine-tuning, pas d'entraînement : modèle pré-entraîné Llama 3 GGUF quantisé (Q4_K_M)
- API locale Ollama : `http://localhost:11434`

---

## Roadmap — 6 phases

### Phase 1 — Ingénierie des données
- [x] Téléchargement DVF Paris (75) — 28 239 transactions 2024
- [x] Intégration DPE (ADEME) — 100 000 diagnostics, 21 communes
- [x] Enrichissement Géorisques — API officielle, 20 communes
- [ ] Intégration Délinquance (Interstats)
- [x] Nettoyage, fusion par Code INSEE

**Livrable :** `dataset_propre_75.csv` — 28 239 lignes, 0 valeur manquante

### Phase 2 — Modélisation prédictive (ML)
- [ ] Split train 80% / test 20%
- [ ] Régression RandomForest + KNN
- [ ] Clustering K-Means (classes de logements)
- [ ] Évaluation : MAE, RMSE, R²

**Livrable :** `modele_estimation.pkl`

### Phase 3 — Outils de l'agent
- [ ] `estimer_prix(surface, lat, lon)`
- [ ] `obtenir_risques_climatiques(lat, lon)`

**Livrable :** `backend/agent/tools.py`

### Phase 4 — Orchestration de l'agent IA
- [ ] Ollama + Llama 3 GGUF en local
- [ ] LangChain → liaison LLM ↔ tools.py
- [ ] Prompt système (rôle expert immobilier + guardrails)

**Livrable :** `backend/agent/agent.py`

### Phase 5 — Interface utilisateur (Streamlit)
- [ ] Carte Folium interactive — clic → latitude/longitude
- [ ] Formulaire (surface, nb pièces, type de bien)
- [ ] Affichage rapport + visualisation interactive
- [ ] Export PDF

**Livrable :** `app.py`

### Phase 6 — Déploiement Cloud (AWS)
- [ ] Dockerfile + docker-compose
- [ ] AWS EC2 t3.micro (Free Tier 12 mois)
- [ ] URL publique accessible par le jury

**Livrable :** URL publique

---

## Structure du projet

```
estimia/
├── app.py                        # Point d'entrée Streamlit (Phase 5)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml                # Config Ruff
├── .gitignore
│
├── backend/
│   ├── main.py                   # Point d'entrée FastAPI
│   ├── requirements.txt
│   ├── api/
│   │   └── estimate.py           # Route POST /estimate
│   ├── agent/
│   │   ├── agent.py              # Orchestration LangChain + Ollama
│   │   └── tools.py              # estimer_prix() + risques_climatiques()
│   ├── ml/
│   │   ├── regression.py         # RandomForest + KNN
│   │   ├── clustering.py         # K-Means
│   │   └── models/
│   │       └── modele_estimation.pkl
│   └── data/
│       ├── pipeline.py           # Pipeline données 
│       ├── raw/
│       └── processed/
│           └── dataset_propre_75.csv
│
├── notebooks/
│   ├── 01_eda_dvf.ipynb
│   ├── 02_regression_experiments.ipynb
│   └── 03_clustering_analysis.ipynb
│
└── docs/
```

---

## Lancement du projet

### Prérequis

- Python 3.11+
- Node.js 18+
- Git

### Étape 1 — Cloner le repo

```bash
git clone https://github.com/<votre-org>/estimia.git
cd estimia
```

### 2. Backend Python

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload --port 8000
```

### 3. Pipeline de données

```bash
cd data
python pipeline.py            # télécharge et nettoie les données
python pipeline.py --skip-download  # si déjà téléchargé
```

### 4. Ollama — LLM local

```bash
ollama pull llama3
ollama serve
# LLM disponible sur http://localhost:11434
```

### 5. Lancer l'application

```bash
cd ../..
streamlit run app.py
```

### 6. Docker

```bash
docker-compose up --build
```

---

## Variables d'environnement

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
GEORISQUES_API=https://georisques.gouv.fr/api/v1
```

---

## Conventions Git

### Branches

| Branche | Rôle |
|---------|------|
| `main` | Production — protégée, merge via PR |
| `develop` | Intégration |
| `feature/data-pipeline` | Phase 1  |
| `feature/ml-regression` | Phase 2 |
| `feature/agent-tools` | Phase 3 |
| `feature/agent-llm` | Phase 4 |
| `feature/frontend` | Phase 5 |
| `feature/deployment` | Phase 6 |

### Format des commits

```
feat(data): DVF pipeline Paris 75 — 28239 transactions
feat(ml): implement RandomForest regression
feat(tools): add estimer_prix and risques_climatiques
feat(agent): integrate Ollama Llama3 with LangChain
feat(frontend): add Folium interactive map
fix(data): update DVF URL 2024
```

---

## Données utilisées

| Source | Contenu | Statut |
|--------|---------|--------|
| DVF (data.gouv.fr) | 28 239 transactions Paris 2024 | ✅ |
| DPE (ADEME) | 100 000 diagnostics, 21 communes | ✅ |
| Géorisques | Risques naturels, 20 communes | ✅ |
| Délinquance (Interstats) | Taux par département | 🔲 |

---

## Licence

Projet académique — données sous licence Etalab (Open Data).