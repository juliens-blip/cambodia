#!/usr/bin/env python3
"""
Combined startup script for Railway.
Runs both FastAPI and Streamlit in the same container.
Version: 3.0 - Robust process management with auto-restart
"""
import os
import subprocess
import sys
import threading
import time
import socket
import urllib.request
import urllib.error
import signal
import atexit
import re

print("=" * 60, flush=True)
print("START.PY LOADED - Version 3.0", flush=True)
print("=" * 60, flush=True)

# Global state for process management
api_process = None
api_lock = threading.Lock()
shutdown_event = threading.Event()
API_PORT = 8000
MAX_RESTART_ATTEMPTS = 5
RESTART_DELAY = 3  # seconds between restart attempts
HEALTH_CHECK_INTERVAL = 30  # seconds between health checks
STARTUP_GRACE_PERIOD = 180  # seconds to allow API startup before health enforcement
api_ready_event = threading.Event()
api_start_time = 0.0


def cleanup():
    """Cleanup function called on exit."""
    global api_process
    print("[CLEANUP] Shutting down...", flush=True)
    shutdown_event.set()
    with api_lock:
        if api_process and api_process.poll() is None:
            print("[CLEANUP] Terminating API process...", flush=True)
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("[CLEANUP] Force killing API process...", flush=True)
                api_process.kill()
    print("[CLEANUP] Done", flush=True)


def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    print(f"[SIGNAL] Received signal {signum}", flush=True)
    cleanup()
    sys.exit(0)


# Register cleanup handlers
atexit.register(cleanup)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def is_port_open(port: int) -> bool:
    """Check if a port is open (non-blocking)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except Exception:
        return False


def wait_for_port(port: int, timeout: int = 60) -> bool:
    """Wait for a port to be available."""
    print(f"[WAIT] Checking port {port}...", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        if shutdown_event.is_set():
            return False
        if is_port_open(port):
            print(f"[WAIT] Port {port} is open!", flush=True)
            return True
        elapsed = int(time.time() - start)
        if elapsed % 10 == 0 and elapsed > 0:
            print(f"[WAIT] Still waiting for port {port}... ({elapsed}s)", flush=True)
        time.sleep(1)
    print(f"[WAIT] Timeout waiting for port {port}", flush=True)
    return False


def test_api_health(port: int = 8000, quiet: bool = False) -> bool:
    """Test if API health endpoint responds."""
    try:
        url = f"http://127.0.0.1:{port}/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode('utf-8')
            if not quiet:
                print(f"[HEALTH] API OK: {data}", flush=True)
            return True
    except urllib.error.URLError as e:
        if not quiet:
            print(f"[HEALTH] API failed: {e}", flush=True)
        return False
    except Exception as e:
        if not quiet:
            print(f"[HEALTH] API error: {e}", flush=True)
        return False


def start_api_process():
    """Start the API subprocess and return the process object."""
    global api_start_time
    print(f"[API] Starting FastAPI on port {API_PORT}...", flush=True)
    print(f"[API] Python: {sys.executable}", flush=True)
    print(f"[API] Working dir: {os.getcwd()}", flush=True)
    api_start_time = time.time()
    api_ready_event.clear()

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn",
         "app.main:app",
         "--host", "0.0.0.0",
         "--port", str(API_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process


def stream_api_output(process):
    """Stream API output in a separate thread."""
    try:
        for line in process.stdout:
            if shutdown_event.is_set():
                break
            print(f"[API] {line.rstrip()}", flush=True)
    except Exception as e:
        if not shutdown_event.is_set():
            print(f"[API] Output stream error: {e}", flush=True)


def run_api_with_restart():
    """Run the API with automatic restart on failure."""
    global api_process
    restart_count = 0
    consecutive_failures = 0

    while not shutdown_event.is_set():
        try:
            with api_lock:
                api_process = start_api_process()
                current_process = api_process

            # Start output streaming in a separate thread
            output_thread = threading.Thread(
                target=stream_api_output,
                args=(current_process,),
                daemon=True
            )
            output_thread.start()

            # Wait for API to be ready
            if wait_for_port(API_PORT, timeout=90):
                print(f"[API] API is ready on port {API_PORT}", flush=True)
                for attempt in range(5):
                    if test_api_health(API_PORT, quiet=True):
                        api_ready_event.set()
                        break
                    time.sleep(2)
                if api_ready_event.is_set():
                    print("[API] API health check passed (ready)", flush=True)
                else:
                    print("[API] API health check not ready yet", flush=True)
                consecutive_failures = 0  # Reset failure counter on success
            else:
                print(f"[API] API failed to start within timeout", flush=True)

            # Monitor the process
            while not shutdown_event.is_set():
                exit_code = current_process.poll()
                if exit_code is not None:
                    print(f"[API] Process exited with code {exit_code}", flush=True)
                    api_ready_event.clear()
                    break
                time.sleep(1)

            # If we're shutting down, don't restart
            if shutdown_event.is_set():
                break

            # Process died unexpectedly - prepare to restart
            consecutive_failures += 1
            restart_count += 1

            if consecutive_failures >= MAX_RESTART_ATTEMPTS:
                print(f"[API] Too many consecutive failures ({consecutive_failures}), giving up", flush=True)
                break

            print(f"[API] Restarting API (attempt {restart_count}, consecutive failures: {consecutive_failures})...", flush=True)
            time.sleep(RESTART_DELAY)

        except Exception as e:
            print(f"[API] Error in API manager: {e}", flush=True)
            if not shutdown_event.is_set():
                consecutive_failures += 1
                if consecutive_failures >= MAX_RESTART_ATTEMPTS:
                    print(f"[API] Too many errors, stopping API manager", flush=True)
                    break
                time.sleep(RESTART_DELAY)

    print("[API] API manager thread ending", flush=True)


def health_monitor():
    """Periodically check API health and log status."""
    # Wait for initial startup
    time.sleep(HEALTH_CHECK_INTERVAL)

    failures_in_a_row = 0
    while not shutdown_event.is_set():
        if not api_ready_event.is_set():
            startup_elapsed = time.time() - api_start_time
            if startup_elapsed < STARTUP_GRACE_PERIOD:
                print(f"[MONITOR] API starting ({startup_elapsed:.0f}s), skipping health check", flush=True)
                time.sleep(HEALTH_CHECK_INTERVAL)
                continue
        if test_api_health(API_PORT, quiet=True):
            if failures_in_a_row > 0:
                print(f"[MONITOR] API recovered after {failures_in_a_row} failed checks", flush=True)
            failures_in_a_row = 0
        else:
            failures_in_a_row += 1
            print(f"[MONITOR] API health check failed ({failures_in_a_row} in a row)", flush=True)

            # If API is down but process is running, it might be stuck
            with api_lock:
                if api_process and api_process.poll() is None and failures_in_a_row >= 3:
                    print("[MONITOR] API process seems stuck, terminating for restart...", flush=True)
                    api_process.terminate()

        # Wait for next check
        for _ in range(HEALTH_CHECK_INTERVAL):
            if shutdown_event.is_set():
                break
            time.sleep(1)

    print("[MONITOR] Health monitor thread ending", flush=True)


def get_streamlit_index_path() -> str | None:
    """Resolve Streamlit's bundled index.html path."""
    try:
        import streamlit
        base_dir = os.path.dirname(streamlit.__file__)
        index_path = os.path.join(base_dir, "static", "index.html")
        if os.path.exists(index_path):
            return index_path
    except Exception as exc:
        print(f"[UI] Warning: could not locate Streamlit index.html: {exc}", flush=True)
    return None


def patch_streamlit_index_html() -> None:
    """Patch Streamlit index.html to force root base URL for _stcore."""
    index_path = get_streamlit_index_path()
    if not index_path:
        print("[UI] Warning: Streamlit index.html not found; skipping base URL patch.", flush=True)
        return

    marker = "<!-- codex:streamlit-base-url-patch -->"
    cache_bust_marker = "<!-- codex:streamlit-cache-bust -->"
    cache_bust_query = "v=codex-baseurl-1"
    injection = (
        f"{marker}\n"
        "<script>\n"
        "  window.__streamlit = window.__streamlit || {};\n"
        "  window.__streamlit.BACKEND_BASE_URL = window.location.origin + \"/\";\n"
        "</script>\n"
    )

    try:
        with open(index_path, "r", encoding="utf-8") as handle:
            html = handle.read()
    except Exception as exc:
        print(f"[UI] Warning: failed to read {index_path}: {exc}", flush=True)
        return

    def insert_injection(content: str) -> str:
        head_tag = "<head>"
        if head_tag in content:
            return content.replace(head_tag, f"{head_tag}\n{injection}", 1)
        if "</head>" in content:
            return content.replace("</head>", f"{injection}</head>", 1)
        return injection + content

    updated = html

    if marker in updated:
        module_index = updated.find('type="module"')
        marker_index = updated.find(marker)
        if module_index != -1 and marker_index > module_index:
            updated = re.sub(
                rf"{re.escape(marker)}\s*<script>.*?</script>\s*",
                "",
                updated,
                count=1,
                flags=re.S,
            )
            updated = insert_injection(updated)
    else:
        updated = insert_injection(updated)

    if cache_bust_query not in updated:
        updated = re.sub(
            r'src="./static/js/index\.([^\"]+)\.js"',
            rf'src="./static/js/index.\1.js?{cache_bust_query}"',
            updated,
            count=1,
        )
        updated = re.sub(
            r'href="./static/css/index\.([^\"]+)\.css"',
            rf'href="./static/css/index.\1.css?{cache_bust_query}"',
            updated,
            count=1,
        )
        if cache_bust_marker not in updated:
            if "</head>" in updated:
                updated = updated.replace("</head>", f"{cache_bust_marker}\n</head>", 1)
            else:
                updated = cache_bust_marker + "\n" + updated

    if updated == html:
        print("[UI] Streamlit index.html already patched.", flush=True)
        return

    try:
        with open(index_path, "w", encoding="utf-8") as handle:
            handle.write(updated)
        print(f"[UI] Patched Streamlit index.html: {index_path}", flush=True)
    except Exception as exc:
        print(f"[UI] Warning: failed to write {index_path}: {exc}", flush=True)


def run_streamlit():
    """Run Streamlit on the main port (Railway's PORT)."""
    port = os.environ.get("PORT", "8501")
    print(f"[UI] Starting Streamlit on port {port}...", flush=True)
    print(f"[UI] API_BASE_URL is: {os.environ.get('API_BASE_URL', 'not set')}", flush=True)

    try:
        patch_streamlit_index_html()
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "ui/streamlit_app.py",
            "--server.port", port,
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[UI] ERROR: Streamlit exited with code {e.returncode}", flush=True)
    except Exception as e:
        print(f"[UI] ERROR: Streamlit failed: {e}", flush=True)


def main():
    print("=" * 60, flush=True)
    print("MAIN FUNCTION STARTED", flush=True)
    print("=" * 60, flush=True)
    print(f"Railway PORT: {os.environ.get('PORT', 'not set')}", flush=True)
    print(f"Python: {sys.executable}", flush=True)
    print(f"CWD: {os.getcwd()}", flush=True)
    print(f"API_BASE_URL: {os.environ.get('API_BASE_URL', 'not set')}", flush=True)
    print("=" * 60, flush=True)

    # Start API manager thread (non-daemon for proper cleanup)
    print("[MAIN] Starting API manager thread...", flush=True)
    api_thread = threading.Thread(target=run_api_with_restart, name="APIManager")
    api_thread.start()
    print("[MAIN] API manager thread started", flush=True)

    # Wait for API to be ready before starting Streamlit
    print("[MAIN] Waiting for API to be ready...", flush=True)
    if wait_for_port(API_PORT, timeout=90):
        print("[MAIN] API port is open!", flush=True)
        time.sleep(2)  # Give uvicorn a moment to fully initialize
        if test_api_health(API_PORT):
            print("[MAIN] API health check passed!", flush=True)
        else:
            print("[MAIN] API health check failed, but continuing...", flush=True)
    else:
        print("[MAIN] API not responding after timeout, starting Streamlit anyway...", flush=True)

    # Set API_BASE_URL for Streamlit
    os.environ["API_BASE_URL"] = f"http://127.0.0.1:{API_PORT}"
    print(f"[MAIN] Set API_BASE_URL to: {os.environ['API_BASE_URL']}", flush=True)

    # Start health monitor thread (daemon - will stop when main exits)
    print("[MAIN] Starting health monitor thread...", flush=True)
    monitor_thread = threading.Thread(target=health_monitor, name="HealthMonitor", daemon=True)
    monitor_thread.start()

    # Run Streamlit in main thread
    print("[MAIN] Starting Streamlit...", flush=True)
    try:
        run_streamlit()
    finally:
        # Streamlit exited - trigger cleanup
        print("[MAIN] Streamlit exited, initiating shutdown...", flush=True)
        shutdown_event.set()

        # Wait for API thread to finish (with timeout)
        api_thread.join(timeout=10)
        if api_thread.is_alive():
            print("[MAIN] API thread didn't stop gracefully", flush=True)


if __name__ == "__main__":
    main()
