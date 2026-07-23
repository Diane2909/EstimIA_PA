# EstimIA — Backend FastAPI (image de production)
FROM python:3.11-slim

WORKDIR /app

# Dépendances système minimales (certificats pour les appels HTTPS sortants)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY api.py tools.py agent.py ./
COPY scripts/download_model.py scripts/download_model.py
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Peuplé au démarrage par entrypoint.sh (téléchargement depuis Azure Blob Storage)
# ou par un volume monté en local (docker-compose)
RUN mkdir -p model

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
