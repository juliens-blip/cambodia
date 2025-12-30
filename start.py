#!/usr/bin/env python3
"""
Combined startup script for Railway.
Runs both FastAPI and Streamlit in the same container.
Version: 2.0 - Fixed connection issues
"""
import os
import subprocess
import sys
import threading
import time
import socket
import urllib.request
import urllib.error

print("=" * 60, flush=True)
print("START.PY LOADED - Version 2.0", flush=True)
print("=" * 60, flush=True)


def wait_for_port(port: int, timeout: int = 60) -> bool:
    """Wait for a port to be available."""
    print(f"[WAIT] Checking port {port}...", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                print(f"[WAIT] Port {port} is open!", flush=True)
                return True
            else:
                elapsed = int(time.time() - start)
                if elapsed % 10 == 0:
                    print(f"[WAIT] Still waiting for port {port}... ({elapsed}s)", flush=True)
        except Exception as e:
            print(f"[WAIT] Socket error: {e}", flush=True)
        time.sleep(1)
    print(f"[WAIT] Timeout waiting for port {port}", flush=True)
    return False


def test_api_health(port: int = 8000) -> bool:
    """Test if API health endpoint responds."""
    try:
        url = f"http://127.0.0.1:{port}/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode('utf-8')
            print(f"[TEST] API health OK: {data}", flush=True)
            return True
    except urllib.error.URLError as e:
        print(f"[TEST] API health failed: {e}", flush=True)
        return False
    except Exception as e:
        print(f"[TEST] API health error: {e}", flush=True)
        return False


def run_api():
    """Run FastAPI in background."""
    port = "8000"  # Internal API port
    print(f"[API] Starting FastAPI on port {port}...", flush=True)
    print(f"[API] Python: {sys.executable}", flush=True)
    print(f"[API] Working dir: {os.getcwd()}", flush=True)
    try:
        # Use Popen to run uvicorn and capture output
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn",
             "app.main:app",
             "--host", "0.0.0.0",
             "--port", port],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        # Stream output
        for line in process.stdout:
            print(f"[API] {line.rstrip()}", flush=True)
        # Wait for process to end
        process.wait()
        print(f"[API] Process ended with code {process.returncode}", flush=True)
    except Exception as e:
        print(f"[API] ERROR: FastAPI crashed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_streamlit():
    """Run Streamlit on the main port (Railway's PORT)."""
    port = os.environ.get("PORT", "8501")
    print(f"[UI] Starting Streamlit on port {port}...", flush=True)
    print(f"[UI] API_BASE_URL is: {os.environ.get('API_BASE_URL', 'not set')}", flush=True)
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
    print("=" * 60, flush=True)
    print("MAIN FUNCTION STARTED", flush=True)
    print("=" * 60, flush=True)
    print(f"Railway PORT: {os.environ.get('PORT', 'not set')}", flush=True)
    print(f"Python: {sys.executable}", flush=True)
    print(f"CWD: {os.getcwd()}", flush=True)
    print(f"API_BASE_URL: {os.environ.get('API_BASE_URL', 'not set')}", flush=True)
    print("=" * 60, flush=True)

    # Start API in background thread
    print("[MAIN] Starting API thread...", flush=True)
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    print("[MAIN] API thread started", flush=True)

    # Wait for API to be ready (up to 90 seconds for model loading)
    print("[MAIN] Waiting for API to be ready on port 8000...", flush=True)
    if wait_for_port(8000, timeout=90):
        print("[MAIN] ✅ Port 8000 is open!", flush=True)
        # Additional health check
        time.sleep(2)  # Give uvicorn a moment to fully start
        if test_api_health(8000):
            print("[MAIN] ✅ API health check passed!", flush=True)
        else:
            print("[MAIN] ⚠️ API health check failed, but port is open", flush=True)
    else:
        print("[MAIN] ❌ API not responding after 90s!", flush=True)
        print("[MAIN] Starting Streamlit anyway...", flush=True)

    # Set API_BASE_URL for Streamlit
    os.environ["API_BASE_URL"] = "http://127.0.0.1:8000"
    print(f"[MAIN] Set API_BASE_URL to: {os.environ['API_BASE_URL']}", flush=True)

    # Run Streamlit in main thread (this is what Railway sees)
    print("[MAIN] Starting Streamlit...", flush=True)
    run_streamlit()


if __name__ == "__main__":
    main()
