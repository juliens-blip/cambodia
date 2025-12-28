#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Installation automatisée des dépendances - Cambodia Agri Analytics
Compatible Python 3.14 (sans ChromaDB)
"""

import subprocess
import sys
import os

def run_command(command: str, description: str) -> bool:
    """Exécute une commande et retourne True si succès"""
    print(f"\n{'='*70}")
    print(f"ETAPE: {description}")
    print(f"{'='*70}")
    print(f"Command: {command}")
    print()

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("WARNINGS:", result.stderr)
        print(f"\n[OK] {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[X] {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Installation complète des dépendances"""

    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║     INSTALLATION AUTOMATIQUE - CAMBODIA AGRI ANALYTICS            ║
    ║                                                                   ║
    ║     Python 3.14 Compatible (sans ChromaDB)                        ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)

    # Vérifier la version Python
    print(f"Python version detectee: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print()

    if sys.version_info < (3, 10):
        print("[X] ERREUR: Python 3.10+ requis")
        return 1

    # Liste des étapes d'installation
    steps = [
        {
            "command": "pip install --upgrade pip",
            "description": "Mise a jour de pip",
            "critical": False
        },
        {
            "command": "pip install --only-binary=:all: numpy>=2.0.0 pandas>=2.1.0",
            "description": "Installation NumPy et Pandas",
            "critical": True
        },
        {
            "command": "pip install --only-binary=:all: supabase>=2.0.0 httpx>=0.25.0",
            "description": "Installation Supabase",
            "critical": True
        },
        {
            "command": "pip install --only-binary=:all: fastapi uvicorn[standard]>=0.24.0 pydantic>=2.5.0 pydantic-settings>=2.1.0",
            "description": "Installation FastAPI stack",
            "critical": True
        },
        {
            "command": "pip install --only-binary=:all: apscheduler>=3.10.0",
            "description": "Installation APScheduler",
            "critical": True
        },
        {
            "command": "pip install --only-binary=:all: google-api-python-client google-auth-httplib2 google-auth-oauthlib",
            "description": "Installation Google API",
            "critical": True
        },
        {
            "command": "pip install --only-binary=:all: PyPDF2 pdf2image pytesseract python-docx",
            "description": "Installation Document Processing",
            "critical": True
        },
        {
            "command": "pip install --only-binary=:all: lxml beautifulsoup4 requests",
            "description": "Installation Web Scraping",
            "critical": True
        },
        {
            "command": "pip install --only-binary=:all: python-dotenv",
            "description": "Installation Utilities",
            "critical": True
        }
    ]

    # Exécuter les étapes
    failed_steps = []
    for i, step in enumerate(steps, 1):
        print(f"\n\n[{i}/{len(steps)}]")
        success = run_command(step["command"], step["description"])

        if not success:
            if step["critical"]:
                print(f"\n[X] ERREUR CRITIQUE: {step['description']} a echoue")
                failed_steps.append(step["description"])
            else:
                print(f"\n[!] WARNING: {step['description']} a echoue (non-critique)")

    # Résumé final
    print("\n\n")
    print("="*70)
    print("RESUME DE L'INSTALLATION")
    print("="*70)

    if not failed_steps:
        print("\n[OK] INSTALLATION COMPLETE!")
        print("\nPackages installes avec succes:")
        print("  - NumPy + Pandas (Data Processing)")
        print("  - FastAPI + Uvicorn (Web Framework)")
        print("  - Supabase (Database + Vector Store)")
        print("  - Google API (Drive Integration)")
        print("  - Document Processing (PDF, DOCX)")
        print("  - Web Scraping (BeautifulSoup, Requests)")
        print("\nNOTE: ChromaDB n'est PAS installe (incompatible Python 3.14)")
        print("      Utiliser Supabase pgvector a la place.")
        print("\nProchaines etapes:")
        print("  1. Executer le test: python test_installation.py")
        print("  2. Lire: INSTALLATION_DIAGNOSTIC.md")
        print("  3. Migrer ChromaDB: CHROMADB_TO_SUPABASE_MIGRATION.md")
        return 0
    else:
        print(f"\n[X] INSTALLATION PARTIELLE ({len(failed_steps)} echecs)")
        print("\nEtapes en echec:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nActions recommandees:")
        print("  1. Verifier la connexion internet")
        print("  2. Verifier que pip fonctionne: pip --version")
        print("  3. Consulter: INSTALLATION_DIAGNOSTIC.md")
        return 1


if __name__ == "__main__":
    try:
        # Fix encoding pour Windows
        if sys.platform == 'win32':
            os.system('chcp 65001 >nul 2>&1')
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[!] Installation interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[X] ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
