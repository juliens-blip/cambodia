@echo off
REM Quick start script for Phase 4 UI

echo ========================================
echo Cambodia Agricultural Intelligence
echo Phase 4: UI ^& API Quick Start
echo ========================================
echo.

REM Check if migration is applied
echo Checking database migration...
python scripts/verify_migration_004.py
if errorlevel 1 (
    echo.
    echo WARNING: Migration 004 not applied!
    echo Please apply migration manually via Supabase SQL Editor:
    echo 1. Go to https://supabase.com/dashboard
    echo 2. Select your project
    echo 3. Navigate to SQL Editor
    echo 4. Execute: supabase/migrations/004_conversation_history.sql
    echo.
    pause
)

echo.
echo Starting services...
echo.

echo [1/2] Starting FastAPI backend (port 8000)...
start "FastAPI Backend" cmd /k "python -m uvicorn app.main:app --reload --port 8000"
timeout /t 3 >nul

echo [2/2] Starting Streamlit frontend (port 8501)...
start "Streamlit Frontend" cmd /k "streamlit run ui/streamlit_app.py"

echo.
echo ========================================
echo Services started!
echo ========================================
echo.
echo Frontend: http://localhost:8501
echo API Docs: http://localhost:8000/docs
echo Health:   http://localhost:8000/health
echo.
echo Press Ctrl+C in each terminal to stop
echo ========================================

pause
