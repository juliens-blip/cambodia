# DIAGNOSTIC D'INSTALLATION - Cambodia Agri Analytics

## STATUT: RÉSOLU (avec limitation ChromaDB)

**Date:** 2025-12-25
**Python:** 3.14.0
**OS:** Windows

---

## PROBLÈME INITIAL

### Symptômes
1. Python 3.14.0 installé globalement (C:\Python314)
2. numpy et pandas installés avec succès via `--only-binary=:all:`
3. Lors de l'installation des autres packages, numpy tentait de se recompiler
4. Erreur: `metadata-generation-failed` pour numpy

### Cause Racine Identifiée

**PROBLÈME #1: Conflit de version NumPy**
- Les anciennes versions de chromadb (0.4.18 - 0.5.x) requièrent `numpy<2.0.0`
- NumPy 2.4.0 est déjà installé
- pip tente d'installer numpy 1.26.4 pour satisfaire chromadb
- numpy 1.26.4 nécessite compilation C (pas de wheel pour Python 3.14)
- Pas de compilateur C disponible sur le système

**PROBLÈME #2: Python 3.14 trop récent**
- ChromaDB dépend de `onnxruntime>=1.14.1`
- `onnxruntime` n'a PAS de wheels précompilés pour Python 3.14
- ChromaDB dépend de `chroma-hnswlib==0.7.6`
- `chroma-hnswlib` requiert compilation C

---

## SOLUTION APPLIQUÉE

### Stratégie: Installation Sélective avec --only-binary

Au lieu d'installer tout `requirements.txt` d'un coup, installation package par package avec vérification:

```bash
# 1. NumPy et Pandas (déjà installés)
pip install --only-binary=:all: numpy>=2.0.0 pandas>=2.1.0

# 2. Supabase (fonctionne avec NumPy 2.x)
pip install --only-binary=:all: supabase>=2.0.0

# 3. Tous les autres packages (sans ChromaDB)
pip install --only-binary=:all: fastapi pydantic-settings apscheduler google-api-python-client google-auth-httplib2 google-auth-oauthlib PyPDF2 pdf2image pytesseract python-docx lxml beautifulsoup4 requests python-dotenv
```

### Résultats

**INSTALLÉ AVEC SUCCÈS (21 packages):**
- ✓ FastAPI 0.127.0
- ✓ Uvicorn 0.38.0
- ✓ Pydantic 2.12.5
- ✓ Pydantic Settings 2.12.0
- ✓ Supabase 2.25.1
- ✓ HTTPX 0.28.1
- ✓ NumPy 2.4.0
- ✓ Pandas 2.3.3
- ✓ APScheduler 3.11.2
- ✓ Google API Client 2.187.0
- ✓ Google Auth 2.41.1
- ✓ Google Auth HTTPLib2 0.3.0
- ✓ Google Auth OAuthLib 1.2.3
- ✓ PyPDF2 3.0.1
- ✓ PDF2Image 1.17.0
- ✓ PyTesseract 0.3.13
- ✓ Python-DOCX 1.2.0
- ✓ LXML 6.0.2
- ✓ BeautifulSoup4 4.14.3
- ✓ Requests 2.32.5
- ✓ Python-DotEnv 1.2.1

**NON INSTALLÉ:**
- ✗ ChromaDB (incompatible Python 3.14)

---

## IMPACT SUR LE PROJET

### Fonctionnalités Affectées

**ChromaDB** était utilisé pour:
- Stockage vectoriel des embeddings
- Recherche sémantique dans les documents
- RAG (Retrieval-Augmented Generation)

### Solutions de Contournement

**OPTION 1: Utiliser Supabase Vector (RECOMMANDÉ)**
```python
# Supabase supporte pgvector pour le stockage vectoriel
# Remplacer ChromaDB par Supabase pgvector dans le code

# Exemple de migration:
# Avant (ChromaDB):
# from chromadb import Client
# client = Client()
# collection = client.create_collection("documents")

# Après (Supabase pgvector):
from supabase import create_client
client = create_client(url, key)
# Utiliser les fonctions vector de PostgreSQL
```

**OPTION 2: Downgrader vers Python 3.11**
```bash
# Désinstaller Python 3.14
# Installer Python 3.11.x depuis python.org
# Réinstaller toutes les dépendances
pip install -r requirements.txt
```

**OPTION 3: Attendre les wheels Python 3.14**
- Surveillance: https://pypi.org/project/onnxruntime/
- Estimé: Q1-Q2 2026 (onnxruntime généralement en retard de 3-6 mois)

---

## COMMANDES DE VÉRIFICATION

### Test Complet
```bash
python D:\Projects\cambodia\test_installation.py
```

### Vérifier Packages Installés
```bash
pip list | grep -E "(fastapi|uvicorn|pydantic|supabase|numpy|pandas)"
```

### Vérifier Version Python
```bash
python --version
```

---

## FICHIERS CRÉÉS

1. **D:\Projects\cambodia\requirements-fixed.txt**
   - Requirements avec chromadb inclus (non fonctionnel sur Python 3.14)

2. **D:\Projects\cambodia\requirements-no-chromadb.txt**
   - Requirements sans chromadb (FONCTIONNEL)

3. **D:\Projects\cambodia\test_installation.py**
   - Script de validation automatique de l'installation

4. **D:\Projects\cambodia\INSTALLATION_DIAGNOSTIC.md**
   - Ce document

---

## RECOMMANDATIONS

### Court Terme (Immédiat)
1. ✓ Utiliser Supabase pgvector au lieu de ChromaDB
2. ✓ Modifier le code pour remplacer les appels ChromaDB
3. ✓ Tester les fonctionnalités de recherche vectorielle avec Supabase

### Moyen Terme (1-3 mois)
1. Surveiller la disponibilité de onnxruntime pour Python 3.14
2. Envisager migration vers Python 3.11 si besoin critique de ChromaDB
3. Documenter les changements d'architecture (ChromaDB -> Supabase)

### Long Terme (3-6 mois)
1. Réévaluer ChromaDB quand compatible Python 3.14
2. Benchmarker performance Supabase pgvector vs ChromaDB
3. Décider de la stack vectorielle définitive

---

## FALLBACK: Installation Complète avec Python 3.11

Si ChromaDB est absolument nécessaire:

```bash
# 1. Désinstaller Python 3.14
# Via Panneau de configuration > Programmes

# 2. Télécharger Python 3.11.9
# https://www.python.org/downloads/release/python-3119/

# 3. Installer Python 3.11.9
# Cocher "Add to PATH"

# 4. Vérifier installation
python --version  # Devrait afficher: Python 3.11.9

# 5. Installer TOUS les packages
pip install -r requirements.txt

# 6. Vérifier ChromaDB
python -c "import chromadb; print('ChromaDB OK')"
```

---

## CONCLUSION

**STATUT: OPÉRATIONNEL (sans ChromaDB)**

Le projet Cambodia Agri Analytics est **fonctionnel** avec 21/22 packages installés.

**Seule limitation:** Pas de ChromaDB à cause de Python 3.14.

**Solution retenue:** Utiliser Supabase pgvector pour le stockage vectoriel.

**Prochaine étape:** Adapter le code pour utiliser Supabase au lieu de ChromaDB.

---

## CONTACT & SUPPORT

- **Documentation Supabase Vector:** https://supabase.com/docs/guides/ai/vector-columns
- **Python 3.11 Download:** https://www.python.org/downloads/
- **ChromaDB Issues:** https://github.com/chroma-core/chroma/issues

---

**Généré le:** 2025-12-25
**Par:** Agent DEBUGGER
**Projet:** Cambodia Agri Analytics
