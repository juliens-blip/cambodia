# Dockerfile optimisé pour Railway
# Utilise une image de base légère pour éviter les problèmes de build

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
    dos2unix \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copier uniquement les fichiers de dépendances d'abord (pour le cache Docker)
COPY requirements-railway.txt ./

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements-railway.txt

# Copier le script de démarrage, convertir en Unix format et le rendre exécutable
COPY start.sh ./
RUN dos2unix start.sh && chmod +x start.sh

# Copier le code de l'application
COPY app/ ./app/

# Exposer le port (Railway définit PORT automatiquement)
EXPOSE 8000

# Commande de démarrage via le script shell
CMD ["./start.sh"]
