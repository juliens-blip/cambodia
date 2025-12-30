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

    # Set API_BASE_URL for internal communication
    os.environ["API_BASE_URL"] = "http://localhost:8000"

    print(f"[UI] API_BASE_URL set to: {os.environ['API_BASE_URL']}", flush=True)
    print(f"[UI] Launching Streamlit...", flush=True)

    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "ui/streamlit_app.py",
            "--server.port", port,
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[UI] ERROR: Streamlit crashed with exit code {e.returncode}", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"[UI] ERROR: Streamlit failed to start: {e}", flush=True)
        sys.exit(1)


def main():
    print("=" * 50, flush=True)
    print("Starting Cambodia Agri Analytics...", flush=True)
    print(f"Railway PORT: {os.environ.get('PORT', 'not set')}", flush=True)
    print(f"Python: {sys.executable}", flush=True)
    print("=" * 50, flush=True)

    # Start API in background thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Wait for API to be ready (up to 90 seconds for model loading)
    print("[STARTUP] Waiting for API to be ready on port 8000...", flush=True)
    if wait_for_port(8000, timeout=90):
        print("[STARTUP] ✅ API is ready!", flush=True)
    else:
        print("[STARTUP] ⚠️ API not responding after 90s, starting Streamlit anyway...", flush=True)

    # Run Streamlit in main thread (this is what Railway sees)
    run_streamlit()


if __name__ == "__main__":
    main()
