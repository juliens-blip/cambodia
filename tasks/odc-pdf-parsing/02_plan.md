# Plan d'Implémentation: ODC & GDrive PDF Parsing

## 📋 Vue d'Ensemble

### Objectifs
- **Primaire**: Extraire 150-200 production records réels depuis 39 PDFs (7 ODC + 32 GDrive)
- **Secondaire**: Éliminer 100% échec de parsing PDF actuel (0/39 PDFs parsés)
- **Technique**: Implémenter approche hybrid (text extraction → OCR fallback)

### Scope
**In Scope:**
- Fix import error `pypdf` → migration vers PyPDF2 compatible
- Ajouter support PDF dans ODC collector `_parse_resource()`
- Créer module partagé `pdf_parser.py` (réutilisable ODC + GDrive)
- Implémenter text extraction + OCR fallback
- Pattern matching pour provinces, production, area, year
- Tests unitaires pour validation

**Out of Scope:**
- Table extraction avec pdfplumber (future enhancement)
- Modification des schémas de base de données
- Traitement des 403 errors Google Drive (déjà géré)
- OCR training personnalisé pour Khmer

### Approche Stratégique
**Hybrid cascading approach:**
```
1. Text Extraction (pypdf/PyPDF2) - Fast, works for modern PDFs
   ↓ (if text < 50 chars or no production data)
2. OCR Fallback (pdf2image + pytesseract) - Thorough, works for scans
   ↓ (if OCR fails)
3. Graceful Degradation - Log error, continue with next PDF
```

---

## 📦 Phase 1: Fix Import Error & Setup (30 min)

### Objectif
Résoudre l'incompatibilité PyPDF et préparer l'environnement

### Tâches

**1.1 Fixer requirements.txt** (10 min)
- Remplacer `PyPDF2>=3.0.0` par `pypdf>=4.0.0`
- **Décision**: Utiliser `pypdf>=4.0.0` (moderne, mieux maintenu)

**1.2 Valider installation** (10 min)
- Exécuter `pip install -r requirements.txt`
- Tester import: `python -c "from pypdf import PdfReader; print('OK')"`
- Tester tesseract: `tesseract --version`

**1.3 Créer structure de test** (10 min)
- Créer `tests/unit/test_pdf_parser.py`
- Setup fixtures avec sample PDF bytes
- Setup mocks pour PyPDF et tesseract

### Fichiers Modifiés
- `requirements.txt` (ligne 27)

### Critères de Succès
- [ ] `pip install -r requirements.txt` succeed sans warnings
- [ ] `from pypdf import PdfReader` fonctionne
- [ ] Structure test créée avec pytest framework

### Risques
- **Tesseract binary manquant**: Mitigation → Rendre OCR optionnel avec graceful warning
- **Conflits de versions**: Mitigation → Pin exact versions tested

---

## 📦 Phase 2: Créer PDF Parser Module Partagé (45 min)

### Objectif
Créer `app/utils/pdf_parser.py` réutilisable par ODC + GDrive

### Tâches

**2.1 Créer classe PDFParser** (20 min)
- Méthode `extract_text(data: bytes) -> str`
  - Tente text extraction avec pypdf
  - Fallback vers OCR si text < 50 chars
  - Gestion exceptions robuste
- Méthode `_extract_text_pypdf(data: bytes) -> str`
  - Limite à 5 premières pages (performance)
  - Return text ou "" si échec
- Méthode `_extract_text_ocr(data: bytes) -> str`
  - Réutilise code existant gdrive_collector.py:254-283
  - Support Khmer + English (lang='khm+eng')
  - Graceful degradation si tesseract manquant

**2.2 Créer méthode pattern matching** (15 min)
- Méthode `extract_production_data(text: str, commodity: str, filename: str) -> List[Dict]`
  - Réutilise patterns de gdrive_collector.py:349-463
  - Regex pour production_tons, area_hectares, year
  - Liste provinces cambodgiennes
  - Return records structurés

**2.3 Tests unitaires** (10 min)
- Test text extraction avec mock PDF
- Test OCR fallback avec mock images
- Test pattern matching avec sample text
- Test graceful degradation (tesseract missing)

### Fichiers Créés
- `app/utils/pdf_parser.py` (~200 lignes)

### Fichiers Modifiés
- `app/utils/__init__.py` (ajouter export PDFParser)

### Code Structure Estimé
```python
# app/utils/pdf_parser.py
class PDFParser:
    def __init__(self):
        self.tesseract_available = self._check_tesseract()

    def extract_text(self, data: bytes) -> str:
        # Try text extraction first
        text = self._extract_text_pypdf(data)
        if text and len(text) > 50:
            return text

        # Fallback to OCR
        if self.tesseract_available:
            text = self._extract_text_ocr(data)

        return text

    def extract_production_data(
        self,
        text: str,
        commodity: str,
        filename: str
    ) -> List[Dict[str, Any]]:
        # Pattern matching logic
        ...
```

### Critères de Succès
- [ ] PDFParser.extract_text() fonctionne avec PDF moderne
- [ ] PDFParser.extract_text() fallback vers OCR pour scans
- [ ] extract_production_data() extrait provinces + production + area
- [ ] Tests passent à 100%
- [ ] Code réutilisable (pas de duplication)

### Risques
- **OCR lent**: Mitigation → Limite 5 pages, async processing
- **Patterns ne matchent pas**: Mitigation → Tests avec vraies données samples

---

## 📦 Phase 3: Intégrer PDF Parser dans ODC Collector (30 min)

### Objectif
Ajouter support PDF dans `odc_collector.py`

### Tâches

**3.1 Modifier _parse_resource()** (15 min)
- Détecter PDFs: `url.endswith('.pdf')` ou `b'%PDF' in data[:10]`
- Ajouter branche PDF avant CSV fallback (ligne ~241)
- Appeler `self._parse_pdf(data, commodity, url)`

**3.2 Implémenter _parse_pdf()** (10 min)
- Instancier PDFParser
- Extraire text: `text = parser.extract_text(data)`
- Extraire production: `records = parser.extract_production_data(text, commodity, filename)`
- Ajouter metadata: source="ODC", extraction_method, extraction_date
- Return records avec logging

**3.3 Tests d'intégration** (5 min)
- Mock httpx client avec sample PDF bytes
- Vérifier _parse_resource() route vers _parse_pdf()
- Vérifier records retournés avec structure correcte

### Fichiers Modifiés
- `app/collectors/odc_collector.py`:
  - Ligne ~10: `from app.utils.pdf_parser import PDFParser`
  - Ligne ~241: Ajouter condition PDF dans `_parse_resource()`
  - Ligne ~350: Ajouter méthode `_parse_pdf()` (~30 lignes)

### Code Structure Estimé
```python
# Dans odc_collector.py _parse_resource()
def _parse_resource(self, data: bytes, commodity: str, url: str):
    # 1. Try PDF (NEW)
    if url.endswith('.pdf') or data[:10].startswith(b'%PDF'):
        return self._parse_pdf(data, commodity, url)

    # 2. Try JSON
    elif url.endswith('.json') or b'{' in data[:100]:
        ...

    # 3. Try Excel
    elif url.endswith(('.xls', '.xlsx')):
        ...

    # 4. Try CSV (default)
    else:
        ...

def _parse_pdf(self, data: bytes, commodity: str, url: str):
    parser = PDFParser()
    text = parser.extract_text(data)

    if not text:
        logger.warning(f"No text extracted from PDF: {url}")
        return []

    records = parser.extract_production_data(
        text, commodity,
        filename=url.split('/')[-1]
    )

    # Add metadata
    for record in records:
        record["source"] = "ODC"
        record["metadata"]["url"] = url
        record["metadata"]["scraped_at"] = datetime.utcnow().isoformat()

    logger.info(f"Parsed {len(records)} records from PDF: {url}")
    return records
```

### Critères de Succès
- [ ] ODC collector détecte PDFs correctement
- [ ] _parse_pdf() extrait texte et données
- [ ] Records structure identique aux CSV/JSON
- [ ] Tests d'intégration passent
- [ ] Logging approprié (INFO + WARNING)

### Risques
- **PDF detection false positives**: Mitigation → Check magic bytes `%PDF`
- **Performance degradation**: Mitigation → Limite 5 pages, timeout 30s

---

## 📦 Phase 4: Refactoriser GDrive Collector (30 min)

### Objectif
Utiliser PDFParser partagé au lieu du code inline

### Tâches

**4.1 Remplacer _extract_text_from_pdf()** (15 min)
- Supprimer méthode inline (lignes 225-283)
- Remplacer par appel `PDFParser().extract_text(content)`
- Maintenir même signature pour rétrocompatibilité

**4.2 Refactoriser _extract_production_from_text()** (10 min)
- Garder méthode actuelle, ajouter appel PDFParser en parallèle
- **Décision**: Garder et appeler PDFParser.extract_production_data()

**4.3 Tests de régression** (5 min)
- Vérifier GDrive collector fonctionne toujours
- Vérifier extraction PDF identique ou améliorée
- Vérifier 17 PDFs précédemment téléchargés

### Fichiers Modifiés
- `app/collectors/gdrive_collector.py`:
  - Ligne ~10: `from app.utils.pdf_parser import PDFParser`
  - Ligne ~225-283: Simplifier `_extract_text_from_pdf()`
  - Optionnel: Ligne ~349-463: Utiliser PDFParser.extract_production_data()

### Code Structure Estimé
```python
# Dans gdrive_collector.py
async def _extract_text_from_pdf(self, content: bytes) -> str:
    """Extract text from PDF using shared parser."""
    parser = PDFParser()
    return parser.extract_text(content)
```

### Critères de Succès
- [ ] Code duplication éliminé
- [ ] GDrive collector tests passent
- [ ] Performance identique ou meilleure
- [ ] Extraction quality ≥ précédente

### Risques
- **Régression fonctionnelle**: Mitigation → Tests complets avant/après
- **Breaking changes**: Mitigation → Gradual refactor, feature flag

---

## 📦 Phase 5: Pattern Matching Optimization (30 min)

### Objectif
Améliorer accuracy des regex patterns et province detection

### Tâches

**5.1 Enrichir patterns de production** (10 min)
- Production: `(\d+[,\d]*\.?\d*)\s*(?:tons|tonnes|ton|MT|metric tons)`
- Area: `(\d+[,\d]*\.?\d*)\s*(?:ha|hectares|hectare|hec)`
- Year: `(?:19|20)\d{2}` (contexte: production, agriculture)
- Support formats Khmer (si présents dans samples)

**5.2 Améliorer province detection** (10 min)
- Liste complète: 25 provinces cambodgiennes
- Variantes: "Kampong Cham" vs "Kompong Cham"
- Case-insensitive matching
- Fuzzy matching optionnel (future: using difflib)

**5.3 Validation et déduplication** (10 min)
- Filtrer records invalides (production=0, province="Unknown")
- Déduplication: (province, year, commodity) unique
- Logging: nombre records avant/après filtering

### Fichiers Modifiés
- `app/utils/pdf_parser.py`:
  - Ligne ~100-150: Méthode `extract_production_data()`

### Critères de Succès
- [ ] Patterns matchent ≥80% des PDFs réels testés
- [ ] Province detection accuracy ≥90%
- [ ] Pas de duplicates dans records retournés
- [ ] False positives < 5%

### Risques
- **Over-matching**: Mitigation → Validation stricte des valeurs numériques
- **Under-matching**: Mitigation → Multiple patterns alternatifs

---

## 📦 Phase 6: Tests de Validation & Documentation (45 min)

### Objectif
Tests end-to-end et documentation complète

### Tâches

**6.1 Tests end-to-end** (20 min)
- Créer `tests/integration/test_pdf_collection.py`
- Test ODC: Mock 3 PDFs (cashew + rubber)
- Test GDrive: Mock 3 PDFs (scan + modern)
- Vérifier records structure et quantité
- Performance: < 10s pour 3 PDFs

**6.2 Tests avec vraies données** (15 min)
- Télécharger 2-3 PDFs réels depuis ODC
- Exécuter collector avec verbose logging
- Valider extraction manuelle vs automatique
- Ajuster patterns si needed

**6.3 Documentation** (10 min)
- Docstrings pour PDFParser
- README: "PDF Parsing" section
- Exemples d'usage
- Troubleshooting guide (tesseract installation)

### Fichiers Créés/Modifiés
- `tests/integration/test_pdf_collection.py` (~150 lignes)
- `README.md` (ajouter section PDF Parsing)
- `tasks/odc-pdf-parsing/03_validation.md` (résultats tests)

### Critères de Succès
- [ ] Tous tests passent (unit + integration)
- [ ] Coverage ≥ 80% pour pdf_parser.py
- [ ] Documentation complète et claire
- [ ] Validation manuelle: ≥15 PDFs parsés avec succès

### Risques
- **Tests flaky**: Mitigation → Mocks robustes, fixtures isolées
- **Documentation outdated**: Mitigation → Liens vers code source

---

## 🗂️ Dépendances et Ordre d'Exécution

### Graphe de Dépendances
```
Phase 1 (Fix imports)
    ↓
Phase 2 (PDFParser module) ← Tests unitaires
    ↓
    ├→ Phase 3 (ODC integration) ← Tests integration
    └→ Phase 4 (GDrive refactor) ← Tests regression
    ↓
Phase 5 (Optimization) ← Tests accuracy
    ↓
Phase 6 (E2E validation)
```

### Ordre Strict
1. Phase 1 DOIT être complétée avant Phase 2
2. Phase 2 DOIT être complétée avant Phase 3 ET Phase 4
3. Phase 3 et 4 peuvent être parallélisées
4. Phase 5 nécessite Phase 2-4 complétées
5. Phase 6 nécessite toutes phases précédentes

---

## 📋 Nouvelles Dépendances

### requirements.txt Changes
```python
# AVANT
PyPDF2>=3.0.0          # ❌ Old version, import incompatible
pdf2image>=1.16.3      # ✅ OK
pytesseract>=0.3.10    # ✅ OK

# APRÈS
pypdf>=4.0.0           # ✅ Modern, bien maintenu
pdf2image>=1.16.3      # ✅ No change
pytesseract>=0.3.10    # ✅ No change
```

### Dépendances Système (Optionnelles)
```bash
# Tesseract OCR (pour Windows)
# Download: https://github.com/UB-Mannheim/tesseract/wiki
# Set TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"

# Poppler (pour pdf2image sur Windows)
# Download: https://blog.alivate.com.au/poppler-windows/
# Set POPPLER_PATH="C:\Program Files\poppler-xx\Library\bin"

# Tessdata (pour Khmer OCR)
# Download: https://github.com/tesseract-ocr/tessdata
# Set TESSDATA_PREFIX="C:\Program Files\Tesseract-OCR\tessdata"
```

**Note**: Si tesseract manquant, PDFParser fallback gracefully vers text extraction uniquement

---

## ⚠️ Risques et Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Tesseract non installé** | HAUTE (50%) | MOYEN | Rendre OCR optionnel, graceful warning, documentation claire |
| **PDFs scannés illisibles** | MOYENNE (30%) | MOYEN | OCR avec preprocessing (rotation, deskew), log quality metrics |
| **Patterns ne matchent pas** | MOYENNE (40%) | HAUTE | Tests avec vraies données, patterns multiples, fuzzy matching |
| **Performance lente** | BASSE (20%) | MOYEN | Limite 5 pages, async processing, timeout 30s |
| **Import conflicts PyPDF** | BASSE (10%) | HAUTE | Pin exact versions, tests CI/CD |
| **Khmer OCR accuracy faible** | MOYENNE (40%) | MOYEN | Fallback English patterns, manual validation samples |
| **Regression GDrive collector** | BASSE (15%) | HAUTE | Tests before/after, feature flag, gradual rollout |

---

## ✅ Tests de Validation

### Tests Unitaires (`tests/unit/test_pdf_parser.py`)
```python
def test_extract_text_pypdf():
    """Test text extraction from modern PDF."""
    # Given: PDF with embedded text
    # When: extract_text(pdf_bytes)
    # Then: Returns text > 50 chars

def test_extract_text_ocr_fallback():
    """Test OCR fallback for scanned PDF."""
    # Given: PDF scan (no embedded text)
    # When: extract_text(pdf_bytes)
    # Then: Calls OCR, returns text

def test_extract_production_data_patterns():
    """Test pattern matching for production data."""
    # Given: Text with "Kampong Cham 2023 1500 tons"
    # When: extract_production_data(text)
    # Then: Returns record with province, year, production

def test_graceful_degradation_no_tesseract():
    """Test fallback when tesseract missing."""
    # Given: Tesseract not available
    # When: extract_text(scanned_pdf)
    # Then: Returns empty string, logs warning (no crash)
```

### Tests d'Intégration (`tests/integration/test_pdf_collection.py`)
```python
async def test_odc_collector_pdf_parsing():
    """Test ODC collector with PDF resource."""
    # Given: Mock ODC dataset with PDF download link
    # When: collector.collect()
    # Then: Records extracted from PDF

async def test_gdrive_collector_pdf_refactor():
    """Test GDrive collector after refactor."""
    # Given: Mock Google Drive with 3 PDFs
    # When: collector.collect()
    # Then: Same or better extraction vs baseline
```

### Critères de Succès Mesurables
1. **Import Error**: 0 errors `No module named 'pypdf'`
2. **PDF Detection**: 39/39 PDFs détectés (100%)
3. **Text Extraction**: ≥25/39 PDFs avec text extracted (64%+)
4. **OCR Fallback**: ≥10/39 PDFs via OCR (26%+)
5. **Production Records**: 150-200 records totaux
6. **Accuracy**: ≥80% records validés manuellement (sample 20 PDFs)
7. **Performance**: < 5s/PDF en moyenne
8. **Tests**: 100% pass rate (unit + integration)
9. **Coverage**: ≥80% pour pdf_parser.py

---

## ⏱️ Timeline Estimée

### Par Phase
| Phase | Tâches | Temps Estimé | Complexité |
|-------|--------|--------------|------------|
| Phase 1: Fix imports | 3 | 30 min | FAIBLE |
| Phase 2: PDFParser module | 3 | 45 min | MOYENNE |
| Phase 3: ODC integration | 3 | 30 min | MOYENNE |
| Phase 4: GDrive refactor | 3 | 30 min | FAIBLE |
| Phase 5: Optimization | 3 | 30 min | MOYENNE |
| Phase 6: Validation | 3 | 45 min | MOYENNE |
| **TOTAL** | **18 tâches** | **3h30 min** | - |

### Buffer pour Risques
- **+20% buffer**: 4h12 total (recommandé)
- **Risque tesseract installation**: +30 min
- **Risque debugging patterns**: +30 min
- **Total conservateur**: 5h12

---

## 🎯 Impact Estimé

### Avant (Actuel)
- **Production records:** 30 (sample data)
- **PDFs téléchargés:** 39 (7 ODC + 32 GDrive)
- **PDFs parsés:** 0 (100% échec)
- **Source:** Sample data synthétique

### Après (Cible)
- **Production records:** 150-200
- **PDFs téléchargés:** 39 (7 ODC + 32 GDrive)
- **PDFs parsés:** 25-30 (64-77% succès)
- **Source:** Vraies données depuis PDFs ODC + GDrive

**Impact:** **5-7× plus de données** + qualité améliorée

---

## 📄 Fichiers Critiques

### Fichiers à Modifier
1. **requirements.txt** (ligne 27) - BLOQUANT
2. **app/collectors/odc_collector.py** (lignes 10, 241, 350) - HIGH PRIORITY
3. **app/collectors/gdrive_collector.py** (lignes 10, 225-283) - MEDIUM PRIORITY
4. **app/utils/__init__.py** - NEW MODULE

### Fichiers à Créer
1. **app/utils/pdf_parser.py** (~200 lignes) - CORE MODULE
2. **tests/unit/test_pdf_parser.py** (~150 lignes) - VALIDATION
3. **tests/integration/test_pdf_collection.py** (~150 lignes) - E2E

---

**Document créé:** `tasks/odc-pdf-parsing/02_plan.md`
**Approche:** APEX (granularité fine 15-30min, testable, mesurable)
**Prochaine étape:** Validation utilisateur → Implémentation Phase 1-6
