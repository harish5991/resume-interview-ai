#!/usr/bin/env python3
"""
Resume Interview AI — Universal Cross-Platform Launcher
Runs both the FastAPI backend and React frontend concurrently on any IDE or operating system (Windows, Mac, Linux).
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def print_banner():
    print("=" * 70)
    print("   🚀 RESUME INTERVIEW AI — UNIVERSAL LAUNCHER")
    print("=" * 70)
    print(f" • Project Directory: {PROJECT_ROOT}")
    print(f" • Backend: FastAPI on http://127.0.0.1:8000")
    print(f" • Frontend: React + Vite on http://localhost:5174")
    print("=" * 70)

def check_dependencies():
    print("\n[1/3] Checking Python dependencies...")
    try:
        import fastapi
        import uvicorn
        import pymupdf
        import docx
        import sklearn
        import reportlab
        print("  ✓ All required Python modules found.")
    except ImportError as e:
        print(f"  ⚠️ Missing dependency ({e}). Installing requirements.txt...")
        req_file = PROJECT_ROOT / "requirements.txt"
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        print("  ✓ Dependencies successfully installed.")

    print("\n[2/3] Checking Frontend node_modules...")
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("  ⚠️ node_modules not found. Running npm install...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.check_call([npm_cmd, "install"], cwd=str(FRONTEND_DIR))
        print("  ✓ npm dependencies successfully installed.")
    else:
        print("  ✓ Frontend node_modules found.")

def run_services():
    print("\n[3/3] Starting Backend and Frontend services...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    # 1. Start Backend
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "backend.app.main:app",
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ]
    print(f"  ▶ Starting Backend: {' '.join(backend_cmd)}")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(PROJECT_ROOT), env=env)

    # Wait 1.5s for backend to initialize
    time.sleep(1.5)

    # 2. Start Frontend
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend_cmd = [npm_cmd, "run", "dev"]
    print(f"  ▶ Starting Frontend: {' '.join(frontend_cmd)}")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(FRONTEND_DIR))

    print("\n" + "=" * 70)
    print("  ✅ BOTH SERVICES ARE LIVE!")
    print("  🌐 Web Application: http://localhost:5174")
    print("  📖 API Documentation (Swagger): http://127.0.0.1:8000/docs")
    print("  (Press Ctrl+C anytime to cleanly stop both services)")
    print("=" * 70 + "\n")

    def handle_sigint(signum, frame):
        print("\nShutting down services cleanly...")
        frontend_proc.terminate()
        backend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        handle_sigint(None, None)

if __name__ == "__main__":
    print_banner()
    check_dependencies()
    run_services()
