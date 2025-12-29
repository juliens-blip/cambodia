#!/usr/bin/env python3
"""
Combined startup script for Railway.
Runs both FastAPI and Streamlit in the same container.
"""
import os
import subprocess
import sys
import threading
import time

def run_api():
    """Run FastAPI in background."""
    port = "8000"  # Internal API port
    print(f"[API] Starting FastAPI on port {port}...")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", port
    ])

def run_streamlit():
    """Run Streamlit on the main port (Railway's PORT)."""
    port = os.environ.get("PORT", "8501")
    print(f"[UI] Starting Streamlit on port {port}...")
    
    # Wait for API to start
    time.sleep(3)
    
    # Set API_BASE_URL for internal communication
    os.environ["API_BASE_URL"] = "http://localhost:8000"
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "ui/streamlit_app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ])

def main():
    print("Starting Cambodia Agri Analytics...")
    print(f"Railway PORT: {os.environ.get('PORT', 'not set')}")
    
    # Start API in background thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Run Streamlit in main thread (this is what Railway sees)
    run_streamlit()

if __name__ == "__main__":
    main()
