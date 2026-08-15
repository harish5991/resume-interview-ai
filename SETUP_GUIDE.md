# 🛠️ Universal Setup & IDE Execution Guide

This guide ensures **Resume Interview AI** runs seamlessly on **any device, operating system (Windows, macOS, Linux), or IDE (VS Code, PyCharm, Cursor, Terminal)**.

---

## ⚡ Option 1: 1-Command Universal Launcher (Recommended)

From the project root directory, run:

### Windows:
```cmd
run.bat
```
*or*
```cmd
python run.py
```

### macOS / Linux:
```bash
./run.sh
```
*or*
```bash
python3 run.py
```

> **What this does automatically:**
> 1. Verifies and installs any missing Python packages from `requirements.txt`.
> 2. Verifies and installs frontend packages via `npm install` if `node_modules` is missing.
> 3. Starts the FastAPI backend (`http://127.0.0.1:8000`) and React frontend (`http://localhost:5174`) concurrently.
> 4. Cleanly handles graceful shutdown on `Ctrl+C`.

---

## 💻 Option 2: Running in VS Code / Cursor / Windsurf

1. Open the project root folder in VS Code (`File -> Open Folder... -> project`).
2. Open the **Run & Debug** tab (`Ctrl+Shift+D` or `Cmd+Shift+D`).
3. Select **"Run Full App (Python Launcher)"** or **"Backend: FastAPI Server"** and click the green Play button.
4. Open the integrated terminal for the frontend:
   ```bash
   cd frontend
   npm run dev
   ```
5. Open your browser at **[http://localhost:5174](http://localhost:5174)**.

---

## 🐍 Option 3: Running in PyCharm

1. Open the `project` folder in PyCharm.
2. Set the Python Interpreter (`Settings / Preferences -> Project -> Python Interpreter` -> select your Python 3.10+ virtual environment).
3. Right-click `backend/app/main.py` -> click **Run 'main'** (or run `run.py`).
4. In PyCharm Terminal:
   ```bash
   cd frontend
   npm run dev
   ```
5. Access the app at **[http://localhost:5174](http://localhost:5174)**.

---

## 🖥️ Option 4: Manual Terminal Setup (Step-by-Step)

### 1. Prerequisites
- **Python 3.10+** (`python --version` or `python3 --version`)
- **Node.js 18+** (`node --version` and `npm --version`)
- *(Optional)* **MongoDB** (If MongoDB is not installed, the app automatically switches to the built-in JSON Database engine).

---

### 2. Backend Setup
```bash
# 1. (Optional) Create virtual environment
python3 -m venv venv

# Activate on Mac/Linux:
source venv/bin/activate
# Activate on Windows:
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start backend server
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 3. Frontend Setup
```bash
# In a new terminal window:
cd frontend

# 1. Install packages
npm install

# 2. Start Vite dev server
npm run dev
```

Open **[http://localhost:5174](http://localhost:5174)** in your browser.

---

## ❓ Troubleshooting Common Cross-Device Issues

### 1. `ModuleNotFoundError: No module named 'backend'`
- **Fix**: The project now has auto-bootstrapping in `backend/__init__.py` and `backend/app/main.py`.
- If running manually, set `PYTHONPATH`:
  - **Mac/Linux**: `export PYTHONPATH=$(pwd)`
  - **Windows (CMD)**: `set PYTHONPATH=%cd%`
  - **Windows (PowerShell)**: `$env:PYTHONPATH = (Get-Location).Path`

### 2. `Port 8000 or 5174 in use`
- **Mac/Linux**: `lsof -t -i :8000 | xargs kill -9`
- **Windows**: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`

### 3. `Proxy error / Connection Refused`
- Make sure the backend is running on `http://127.0.0.1:8000` before interacting with the frontend.
- Check backend health at `http://127.0.0.1:8000/api/health`.

### 4. `reportlab / fitz not found`
- Run: `pip install -r requirements.txt`
