# Dockerfile combiné pour Railway
# Lance API FastAPI + Streamlit UI dans le même conteneur

FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8501 \
    API_BASE_URL=http://localhost:8000

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copier les fichiers de dépendances
COPY requirements-streamlit.txt ./
COPY requirements-railway.txt ./

# Installer les dépendances (API + Streamlit)
RUN pip install --no-cache-dir -r requirements-railway.txt -r requirements-streamlit.txt

# Copier le script de démarrage
COPY start.py ./

# Copier le code
COPY app/ ./app/
COPY ui/ ./ui/

# Exposer les ports
EXPOSE 8000 8501

# Démarrage combiné
CMD ["python", "start.py"]
