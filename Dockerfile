# Dockerfile optimisé pour Railway
# Utilise une image de base légère

FROM python:3.11-slim-bookworm

# Définir le répertoire de travail
WORKDIR /app

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copier uniquement les fichiers de dépendances d'abord (pour le cache Docker)
COPY requirements-railway.txt ./

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements-railway.txt

# Copier le script de démarrage Python
COPY start.py ./

# Copier le code de l'application
COPY app/ ./app/

# Exposer le port
EXPOSE 8000

# Commande de démarrage via Python (lit correctement $PORT)
CMD ["python", "start.py"]
