#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test d'installation des dépendances - Cambodia Agri Analytics"""

import sys
import os
from typing import Dict, List, Tuple

# Fix encoding pour Windows
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

def test_imports() -> Tuple[List[str], List[str]]:
    """Teste l'importation de tous les packages critiques"""

    successful = []
    failed = []

    # Liste des packages à tester
    tests = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("pydantic_settings", "Pydantic Settings"),
        ("supabase", "Supabase"),
        ("httpx", "HTTPX"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("apscheduler", "APScheduler"),
        ("googleapiclient", "Google API Client"),
        ("google.auth", "Google Auth"),
        ("google_auth_httplib2", "Google Auth HTTPLib2"),
        ("google_auth_oauthlib", "Google Auth OAuthLib"),
        ("PyPDF2", "PyPDF2"),
        ("pdf2image", "PDF2Image"),
        ("pytesseract", "PyTesseract"),
        ("docx", "Python-DOCX"),
        ("lxml", "LXML"),
        ("bs4", "BeautifulSoup4"),
        ("requests", "Requests"),
        ("dotenv", "Python-DotEnv"),
    ]

    for module_name, display_name in tests:
        try:
            __import__(module_name)
            successful.append(display_name)
            print(f"[OK] {display_name:<25} OK")
        except ImportError as e:
            failed.append(f"{display_name}: {str(e)}")
            print(f"[X] {display_name:<25} FAILED: {e}")

    return successful, failed


def test_critical_packages() -> Dict[str, str]:
    """Teste les packages critiques avec vérification de version"""

    results = {}

    try:
        import numpy as np
        results['numpy'] = f"[OK] NumPy {np.__version__}"
        print(f"NumPy version: {np.__version__}")
    except Exception as e:
        results['numpy'] = f"[X] NumPy FAILED: {e}"

    try:
        import pandas as pd
        results['pandas'] = f"[OK] Pandas {pd.__version__}"
        print(f"Pandas version: {pd.__version__}")
    except Exception as e:
        results['pandas'] = f"[X] Pandas FAILED: {e}"

    try:
        import fastapi
        results['fastapi'] = f"[OK] FastAPI {fastapi.__version__}"
        print(f"FastAPI version: {fastapi.__version__}")
    except Exception as e:
        results['fastapi'] = f"[X] FastAPI FAILED: {e}"

    try:
        import supabase
        results['supabase'] = f"[OK] Supabase (importe avec succes)"
        print(f"Supabase: OK")
    except Exception as e:
        results['supabase'] = f"[X] Supabase FAILED: {e}"

    return results


def main():
    """Fonction principale"""

    print("=" * 70)
    print("TEST D'INSTALLATION - CAMBODIA AGRI ANALYTICS")
    print("=" * 70)
    print()

    print("1. TEST DES IMPORTS")
    print("-" * 70)
    successful, failed = test_imports()
    print()

    print("2. TEST DES PACKAGES CRITIQUES")
    print("-" * 70)
    results = test_critical_packages()
    print()

    print("=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    print(f"Packages installés avec succès: {len(successful)}")
    print(f"Packages en échec: {len(failed)}")
    print()

    if failed:
        print("PACKAGES MANQUANTS OU EN ÉCHEC:")
        for fail in failed:
            print(f"  - {fail}")
        print()

    # Test ChromaDB séparément car non installé
    print("NOTES:")
    print("  - ChromaDB n'est PAS installé (incompatible Python 3.14)")
    print("  - Raison: onnxruntime n'a pas de wheels pour Python 3.14")
    print("  - SOLUTION TEMPORAIRE: Utiliser uniquement Supabase pour le vector store")
    print("  - SOLUTION PERMANENTE: Downgrader vers Python 3.11 ou attendre wheels Python 3.14")
    print()

    if len(failed) == 0:
        print("[OK] INSTALLATION REUSSIE (sauf ChromaDB)")
        return 0
    else:
        print("[X] INSTALLATION PARTIELLE")
        return 1


if __name__ == "__main__":
    sys.exit(main())
