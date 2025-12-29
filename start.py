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
import socket


def wait_for_port(port: int, timeout: int = 60) -> bool:
    """Wait for a port to be available."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def run_api():
    """Run FastAPI in background."""
    port = "8000"  # Internal API port
    print(f"[API] Starting FastAPI on port {port}...", flush=True)
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", port
        ], check=True)
    except Exception as e:
        print(f"[API] ERROR: FastAPI crashed: {e}", flush=True)
        sys.exit(1)


def run_streamlit():
    """Run Streamlit on the main port (Railway's PORT)."""
    port = os.environ.get("PORT", "8501")
    print(f"[UI] Starting Streamlit on port {port}...", flush=True)

    # DON'T wait for API - start Streamlit immediately so Railway sees a process
    # The UI will show temporary errors while API loads, but container won't be killed
    print("[UI] Starting Streamlit immediately (API may still be loading)...", flush=True)

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
    print("=" * 50, flush=True)
    print("Starting Cambodia Agri Analytics...", flush=True)
    print(f"Railway PORT: {os.environ.get('PORT', 'not set')}", flush=True)
    print(f"Python: {sys.executable}", flush=True)
    print("=" * 50, flush=True)

    # Start API in background thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Run Streamlit in main thread (this is what Railway sees)
    run_streamlit()


if __name__ == "__main__":
    main()
