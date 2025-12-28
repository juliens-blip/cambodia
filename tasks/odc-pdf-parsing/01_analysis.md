# Analyse: ODC PDF Parsing Implementation

## 📋 Contexte
**Date:** 2025-12-25
**Demande:** Implémenter PDF parsing pour extraire données des 7 datasets ODC découverts
**Objectif:** Passer de 30 sample records à 150-200 production records réels depuis PDFs
**Priority:** HIGH (suite amélioration ODC scraper)

---

## 🔍 État Actuel de la Codebase

### Fichiers Concernés

| Fichier | Type | Rôle | Lignes |
|---------|------|------|--------|
| `app/collectors/odc_collector.py` | Collector principal | Parse CSV/JSON/Excel, **pas PDF** | 468 |
| `app/collectors/gdrive_collector.py` | Collector Google Drive | Télécharge 32 PDFs, **parsing échoue** | ~500 |
| `requirements.txt` | Dépendances | PyPDF2>=3.0.0, pdf2image, pytesseract | 70 |

---

## 🐛 Problème Principal: Import Error PyPDF

### État Actuel du Code

**ODC Collector - `_parse_resource()` (lignes 208-257):**
```python
def _parse_resource(self, data: bytes, commodity: str, url: str):
    # 1. Try JSON
    if url.endswith('.json') or b'{' in data[:100]:
        ...

    # 2. Try Excel
    elif url.endswith(('.xls', '.xlsx')):
        records = self._parse_excel(data, commodity, url)

    # 3. Try CSV (default)
    else:
        # ❌ PDF binaire traité comme CSV → UTF-8 decode error
        text = data.decode('utf-8', errors='ignore')
        ...
```

**Problème:** Aucun support PDF - les fichiers binaires causent des erreurs

**GDrive Collector - Import Error (ligne 238):**
```python
from pypdf import PdfReader  # ❌ ERROR: No module named 'pypdf'
```

**Requirements.txt:**
```
PyPDF2>=3.0.0          # Installé mais jamais importé
```

**Incompatibilité:** Code utilise `pypdf` (nouveau nom) mais requirements.txt a `PyPDF2` (ancien nom)

---

## 💻 Librairies PDF Disponibles

### Tableau Comparatif

| Librairie | Version | Installée | Importée | Statut | Capabilities |
|-----------|---------|-----------|----------|--------|--------------|
| **PyPDF2** | >=3.0.0 | ✅ | ❌ | Inutilisée | Text extraction basique |
| **pypdf** | - | ❌ | ✅ | **IMPORT ERROR** | Text extraction moderne |
| **pdf2image** | >=1.16.3 | ✅ | ✅ | OK | PDF → Images (pour OCR) |
| **pytesseract** | >=0.3.10 | ✅ | ✅ | OK | OCR Khmer + English |
| **pdfplumber** | - | ❌ | ❌ | Manquante | Table extraction structurée |
| **tabula-py** | - | ❌ | ❌ | Manquante | Table extraction Java |

### Evidence des Logs

**GDrive Collector - 17 erreurs (2025-12-25 22:38):**
```
WARNING: PDF text extraction failed: No module named 'pypdf'
WARNING: PDF text extraction failed: No module named 'pypdf'
... (17 fois)
```

**Résultat:** 32 PDFs téléchargés, 0 PDFs parsés (100% échec)

---

## 📁 Les 7 Datasets PDF Découverts

### ODC Collector - 7 Datasets Découverts

**Cashew:** 3 datasets
**Rubber:** 4 datasets

**Ressources téléchargées:** 7 PDFs (tous échouent au parsing)

**Erreurs typiques:**
```
ERROR: 'utf-8' codec can't decode byte 0x9c in position 288
ERROR: 'utf-8' codec can't decode byte 0xe2 in position 10
```

### GDrive Collector - 32 PDFs Téléchargés

**Statut:**
- 17 PDFs téléchargés avec succès (HTTP 200)
- 14 PDFs access denied (HTTP 403)
- 0 PDFs parsés (import error bloque tout)

**Exemples de fichiers:**
```
1CkkjWIW3-Ryw8APPSPn-qsRX7Mz7rLCv   (PDF) ✓ 200
1idf-OQWGAKbromTBnboH3NMS6bal7UYF   (PDF) ✓ 200
1tN0tq1EQampPePByzZOaeWP1fhkPMqgj   (PDF) ✓ 200
... (17 total)
```

---

## 📊 Structure des Données Attendue

### Format de Production Records

```python
{
    "commodity": "cashew" | "rubber",   # Déterminé du dossier/filename
    "year": int,                        # Extrait du PDF ou filename
    "province": str,                    # Extrait du texte du PDF
    "production_tons": float,           # Extrait du PDF (tables/texte)
    "area_hectares": float,             # Extrait du PDF (tables/texte)
    "source": "ODC" | "GDrive",        # Selon collector
    "metadata": {
        "filename": str,                # Nom du fichier PDF
        "extracted_method": "text_extraction" | "ocr" | "table_extraction",
        "extraction_date": str,         # ISO datetime
        "file_id": str,                 # Google Drive file ID (GDrive)
        "url": str,                     # Dataset URL (ODC)
        "language": "khmer" | "english" | "mixed"
    }
}
```

### Patterns de Détection

**Production (tonnes):**
```regex
(\d+[,\d]*\.?\d*)\s*(?:tons|tonnes|ton|MT)
```

**Area (hectares):**
```regex
(\d+[,\d]*\.?\d*)\s*(?:ha|hectares|hectare)
```

**Year:**
```regex
(?:19|20)\d{2}
```

**Provinces (liste connue):**
```python
provinces = [
    "Kampong Cham", "Kampong Thom", "Kratie",
    "Mondulkiri", "Ratanakiri", "Kampot",
    "Battambang", "Siem Reap", ...
]
```

---

## 💡 Approches Possibles

### Option 1: Text Extraction Simple ⭐ RECOMMANDÉE (Court terme)

**Librairie:** pypdf (ou PyPDF2 fallback)

**Approche:**
```python
from pypdf import PdfReader  # ou PyPDF2
import io

def _parse_pdf_text(data: bytes, commodity: str, url: str):
    reader = PdfReader(io.BytesIO(data))
    text = ""

    # Extract first 5 pages (performance)
    for page in reader.pages[:5]:
        text += page.extract_text()

    # Pattern matching
    production_match = re.search(r'(\d+[,\d]*\.?\d*)\s*(?:tons|tonnes)', text)
    area_match = re.search(r'(\d+[,\d]*\.?\d*)\s*(?:ha|hectares)', text)
    year_match = re.search(r'(?:19|20)\d{2}', text)

    # Return parsed record
    ...
```

**Avantages:**
- ✅ Rapide (< 1 sec/PDF)
- ✅ Aucune dépendance externe
- ✅ Fonctionne sur PDFs modernes avec texte intégré

**Inconvénients:**
- ❌ Ne fonctionne pas sur scans (PDFs image-only)
- ❌ Nécessite extraction de patterns simples
- ❌ Qualité dépend de la structure du PDF

**Dépendances:**
```python
# Corriger requirements.txt:
pypdf>=3.17.0  # (remplacer PyPDF2>=3.0.0)
```

---

### Option 2: OCR avec Tesseract ⭐ RECOMMANDÉE (Complet)

**Librairies:** pdf2image + pytesseract (déjà installées!)

**Approche:**
```python
from pdf2image import convert_from_bytes
from pytesseract import image_to_string

def _parse_pdf_ocr(data: bytes, commodity: str, url: str):
    # Convert PDF → Images
    images = convert_from_bytes(data, first_page=1, last_page=5)

    # OCR chaque page (Khmer + English)
    text = ""
    for image in images:
        text += image_to_string(
            image,
            lang='eng+khm',
            config='--psm 6'
        )

    # Pattern matching (same as option 1)
    ...
```

**Avantages:**
- ✅ Fonctionne sur scans ET PDFs modernes
- ✅ Support Khmer + English
- ✅ Librairies déjà installées

**Inconvénients:**
- ❌ Plus lent (~5-10 sec/PDF)
- ❌ Nécessite tesseract binary installé (système)
- ❌ Moins précis que text extraction pour PDFs modernes

**Dépendances:**
```
pdf2image>=1.16.3      (déjà installé ✅)
pytesseract>=0.3.10    (déjà installé ✅)
tesseract binary       (système - à vérifier)
```

**Code existe déjà:** `gdrive_collector.py:254-283` (réutilisable!)

---

### Option 3: Table Extraction Spécialisée (Futur)

**Librairie:** pdfplumber (à installer)

**Approche:**
```python
import pdfplumber

def _parse_pdf_tables(data: bytes, commodity: str, url: str):
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            if page.tables:
                # Extract table as DataFrame
                df = pd.DataFrame(page.extract_table())

                # Parse like CSV
                records = self._parse_dataframe(df, commodity, url)
                return records
```

**Avantages:**
- ✅ Idéal pour production statistics (données tabulaires)
- ✅ Extraction structurée (colonnes nommées)
- ✅ Qualité excellente pour données numériques

**Inconvénients:**
- ❌ Librairie supplémentaire à installer
- ❌ Lent (~2-3 sec/PDF)
- ❌ Nécessite détection de tables

**Installation:**
```bash
pip install pdfplumber
```

---

### Option 4: Hybrid Approach ⭐⭐ RECOMMANDÉE (Production)

**Stratégie en cascade:**
```python
def _parse_pdf(data: bytes, commodity: str, url: str):
    # 1. Try text extraction (fast)
    records = self._parse_pdf_text(data, commodity, url)
    if records:
        return records

    # 2. Fallback to OCR (thorough)
    records = self._parse_pdf_ocr(data, commodity, url)
    if records:
        return records

    # 3. Fallback to sample data (graceful)
    logger.warning(f"PDF parsing failed for {url} - using sample data")
    return []
```

**Avantages:**
- ✅ Rapide pour PDFs modernes (text extraction)
- ✅ Robuste pour scans (OCR fallback)
- ✅ Graceful degradation

**Inconvénients:**
- ⚠️ Complexité accrue
- ⚠️ Nécessite tests extensifs

---

## ⚠️ Risques et Points d'Attention

### Tableau des Risques

| Risque | Sévérité | Impact | Probabilité | Mitigation |
|--------|----------|--------|-------------|-----------|
| **Scans PDF sans OCR** | HAUTE | 0 données extraites | MOYENNE | Implémenter OCR fallback (Option 2) |
| **Pas de données numériques** | HAUTE | Regex patterns ne matchent rien | BASSE | Tester samples avant déploiement |
| **PDF corrompus/binaires** | MOYENNE | Exception lors parsing | BASSE | Try/except robuste + logging |
| **Khmer text parsing** | MOYENNE | Extraction provinces échoue | MOYENNE | Utiliser détection Khmer (déjà impl.) |
| **Performance** | BASSE | Collection lente | BASSE | Limiter à 5 pages max, async |
| **Google Drive 403 errors** | MOYENNE | 50% fichiers inaccessibles | HAUTE | Déjà géré - fallback public URL |
| **Tesseract not installed** | CRITIQUE | OCR fallback échoue | BASSE | Rendre optionnel avec graceful degradation |

### Questions Critiques à Clarifier

1. **Format des PDFs:** Sont-ils scannés ou modernes (avec texte intégré)?
2. **Langues:** Khmer seulement, English, ou mélangé?
3. **Structures:** Tables régulières ou données éparses?
4. **Métadonnées:** Year/commodity dans filename ou seulement dans le PDF?
5. **Tesseract installé?** Vérifier si tesseract binary est disponible sur le système

---

## 📈 Impact Potentiel

### Avant (Actuel)

- **Production records:** 30 (sample data)
- **PDFs téléchargés:** 39 (7 ODC + 32 GDrive)
- **PDFs parsés:** 0 (100% échec)
- **Source:** Sample data synthétique

### Après (Cible)

- **Production records:** 150-200
- **PDFs téléchargés:** 39 (7 ODC + 32 GDrive)
- **PDFs parsés:** 20-30 (50-80% succès estimé)
- **Source:** Vraies données depuis PDFs ODC + GDrive

**Impact:** **5-7× plus de données** + qualité améliorée

---

## 📊 Résumé Exécutif

1. **Problème principal:** Import error `pypdf` vs `PyPDF2` bloque tout parsing PDF (39 PDFs disponibles, 0 parsés)

2. **Opportunité immédiate:** Fix import + text extraction simple = 20-30 records réels rapidement

3. **Approche recommandée:** Hybrid (text extraction + OCR fallback) pour robustesse production

4. **Dépendances disponibles:** pdf2image + pytesseract déjà installés, code OCR existe dans gdrive_collector

5. **Impact potentiel:** Passer de 30 sample records à 150-200 production records réels en parsant les 39 PDFs

---

**Fichier d'analyse créé:** `tasks/odc-pdf-parsing/01_analysis.md`
**Prochaine étape:** `/plan` pour définir la stratégie d'implémentation détaillée
