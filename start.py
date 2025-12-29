#!/usr/bin/env python3
"""
Startup script for Streamlit on Railway.
Uses Python to read PORT environment variable correctly.
"""
import os
import subprocess
import sys

def main():
    # Get PORT from environment, default to 8501 (Streamlit default)
    port = os.environ.get("PORT", "8501")
    
    print(f"Starting Streamlit on port {port}...")
    
    # Run streamlit with the correct port
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "ui/streamlit_app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    # Replace current process
    os.execvp(sys.executable, cmd)

if __name__ == "__main__":
    main()
