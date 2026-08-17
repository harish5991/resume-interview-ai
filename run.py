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
import socket
import argparse
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks if a network port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def wait_for_port(port: int, timeout: float = 10.0, host: str = "127.0.0.1") -> bool:
    """Waits until a port is open and listening."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port, host):
            return True
        time.sleep(0.3)
    return False

def free_port(port: int):
    """Attempts to cleanly terminate any lingering stale process on the port."""
    if not is_port_in_use(port):
        return
    print(f"  ℹ️ Port {port} is occupied. Cleaning up stale process...")
    try:
        if os.name == "nt":
            # Windows netstat/taskkill
            out = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            for line in out.strip().split('\n'):
                parts = line.strip().split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    pid = parts[-1]
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # macOS / Linux lsof/kill
            out = subprocess.check_output(f'lsof -ti :{port}', shell=True).decode()
            for pid in out.strip().split():
                if pid:
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(0.2)
    except Exception:
        pass

def print_banner(backend_only: bool = False, frontend_only: bool = False):
    print("=" * 70)
    print("   🚀 RESUME INTERVIEW AI — UNIVERSAL LAUNCHER")
    print("=" * 70)
    print(f" • Project Directory: {PROJECT_ROOT}")
    if not frontend_only:
        print(f" • Backend: FastAPI on http://127.0.0.1:8000")
    if not backend_only:
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

def run_services(backend_only: bool = False, frontend_only: bool = False):
    print("\n[3/3] Starting services...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    backend_proc = None
    frontend_proc = None

    # 1. Start Backend
    if not frontend_only:
        free_port(8000)
        backend_cmd = [
            sys.executable, "-m", "uvicorn", "backend.app.main:app",
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ]
        print(f"  ▶ Starting Backend: {' '.join(backend_cmd)}")
        backend_proc = subprocess.Popen(backend_cmd, cwd=str(PROJECT_ROOT), env=env)
        
        # Verify backend readiness
        if wait_for_port(8000, timeout=6.0):
            print("  ✓ Backend FastAPI is ready and listening on port 8000.")
        else:
            print("  ⚠️ Backend is taking longer than usual to start. Checking logs...")

    # 2. Start Frontend
    if not backend_only:
        free_port(5174)
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        frontend_cmd = [npm_cmd, "run", "dev"]
        print(f"  ▶ Starting Frontend: {' '.join(frontend_cmd)}")
        frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(FRONTEND_DIR))

    print("\n" + "=" * 70)
    print("  ✅ SERVICES ARE LIVE!")
    if not backend_only:
        print("  🌐 Web Application: http://localhost:5174")
    if not frontend_only:
        print("  📖 API Documentation (Swagger): http://127.0.0.1:8000/docs")
        print("  🩺 API Health Check: http://127.0.0.1:8000/health")
    print("  (Press Ctrl+C anytime to cleanly stop all services)")
    print("=" * 70 + "\n")

    def handle_sigint(signum, frame):
        print("\nShutting down services cleanly...")
        if frontend_proc:
            frontend_proc.terminate()
        if backend_proc:
            backend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    try:
        while True:
            time.sleep(1)
            if backend_proc and backend_proc.poll() is not None:
                print(f"\n⚠️ Backend process exited with code {backend_proc.returncode}")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                print(f"\n⚠️ Frontend process exited with code {frontend_proc.returncode}")
                break
    except KeyboardInterrupt:
        handle_sigint(None, None)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resume Interview AI Universal Launcher")
    parser.add_argument("--backend-only", action="store_true", help="Start only the FastAPI backend")
    parser.add_argument("--frontend-only", action="store_true", help="Start only the Vite frontend")
    args = parser.parse_args()

    print_banner(backend_only=args.backend_only, frontend_only=args.frontend_only)
    check_dependencies()
    run_services(backend_only=args.backend_only, frontend_only=args.frontend_only)
