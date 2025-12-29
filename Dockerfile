# Dockerfile pour Streamlit UI sur Railway

FROM python:3.11-slim-bookworm

# Définir le répertoire de travail
WORKDIR /app

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8501

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copier les fichiers de dépendances
COPY requirements-streamlit.txt ./

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements-streamlit.txt

# Copier le script de démarrage
COPY start.py ./

# Copier le code de l'application
COPY app/ ./app/
COPY ui/ ./ui/

# Exposer le port Streamlit
EXPOSE 8501

# Commande de démarrage via Python
CMD ["python", "start.py"]
