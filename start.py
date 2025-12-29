#!/usr/bin/env python3
"""
Startup script for Railway deployment.
Uses Python to read PORT environment variable correctly.
"""
import os
import sys

def main():
    # Get PORT from environment, default to 8000
    port = os.environ.get("PORT", "8000")
    
    print(f"Starting uvicorn on port {port}...")
    
    # Use os.execvp to replace current process with uvicorn
    os.execvp("uvicorn", [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", port
    ])

if __name__ == "__main__":
    main()
