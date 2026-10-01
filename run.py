"""Simplified Unified CLI Runner for E-Commerce Database Testing Framework.

Usage:
  python run.py start           # Starts MySQL and FastAPI servers
  python run.py stop            # Stops running servers
  python run.py status          # Checks health of MySQL and FastAPI
  python run.py init-db         # Initializes and seeds the database
  python run.py test            # Runs all tests
  python run.py test --db       # Runs database tests
  python run.py test --api      # Runs API tests
  python run.py test --ui       # Runs UI tests (headless)
  python run.py test --ui --headed  # Runs UI tests with visible browser window
  python run.py test --e2e      # Runs integration and end-to-end tests
  python run.py report          # Opens HTML test report in browser
"""

import sys
import os
import subprocess
import time
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = ROOT_DIR / "venv" / "Scripts" / "python.exe"
VENV_PYTEST = ROOT_DIR / "venv" / "Scripts" / "pytest.exe"
VENV_UVICORN = ROOT_DIR / "venv" / "Scripts" / "uvicorn.exe"
MYSQLD = ROOT_DIR / "mariadb" / "bin" / "mysqld.exe"
DATA_DIR = ROOT_DIR / "mariadb" / "data"
REPORT_HTML = ROOT_DIR / "reports" / "pytest-report.html"

# If run from outside the virtual environment, re-delegate to venv python
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    res = subprocess.run([str(VENV_PYTHON), str(Path(__file__).resolve())] + sys.argv[1:])
    sys.exit(res.returncode)

# Fallback to system python if venv not found
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
PYTEST_EXE = str(VENV_PYTEST) if VENV_PYTEST.exists() else "pytest"

def check_status() -> dict:
    """Checks the health of MySQL and FastAPI."""
    status = {"mysql": False, "fastapi": False}
    # Check MySQL
    try:
        import mysql.connector
        conn = mysql.connector.connect(host="127.0.0.1", port=3306, user="root", password="", database="ecommerce_test")
        status["mysql"] = conn.is_connected()
        conn.close()
    except Exception:
        status["mysql"] = False

    # Check FastAPI
    try:
        import requests
        r = requests.get("http://127.0.0.1:8000/health", timeout=2)
        status["fastapi"] = (r.status_code == 200 and r.json().get("status") == "healthy")
    except Exception:
        status["fastapi"] = False

    return status

def print_status():
    """Prints status of background services."""
    s = check_status()
    print("\n[SERVICES STATUS]")
    print(f"  MySQL Database (3306) : {'[ONLINE]' if s['mysql'] else '[OFFLINE]'}")
    print(f"  FastAPI Server (8000) : {'[ONLINE]' if s['fastapi'] else '[OFFLINE]'}")
    if s["fastapi"]:
        print("  Web Store UI          : http://127.0.0.1:8000")
        print("  API Documentation     : http://127.0.0.1:8000/docs")
    print()

def start_services():
    """Starts MySQL and FastAPI in background if not already running."""
    s = check_status()
    print("\nStarting services...")
    if not s["mysql"]:
        if MYSQLD.exists():
            print("  Starting MySQL server...")
            subprocess.Popen(
                [str(MYSQLD), f"--datadir={DATA_DIR}", "--port=3306", "--console"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)
        else:
            print("  [WARN] Local MariaDB binary not found. Ensure MySQL is running on port 3306.")

    if not s["fastapi"]:
        print("  Starting FastAPI server...")
        subprocess.Popen(
            [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)

    print_status()

def stop_services():
    """Stops local mysqld and uvicorn processes on Windows."""
    print("\nStopping services...")
    try:
        subprocess.run(["taskkill", "/F", "/IM", "mysqld.exe", "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    try:
        subprocess.run(["taskkill", "/F", "/IM", "uvicorn.exe", "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    time.sleep(1)
    print("  All local background services stopped.")
    print_status()

def init_db():
    """Initializes and seeds the database."""
    print("\nInitializing database schema and seed data...")
    subprocess.run([PYTHON_EXE, str(ROOT_DIR / "database" / "db_setup.py"), "init"])

def run_tests(args: list):
    """Executes pytest with simplified options."""
    s = check_status()
    if not s["mysql"] or not s["fastapi"]:
        print("\n[NOTE] Starting services before running tests...")
        start_services()

    cmd = [PYTEST_EXE, "-v"]

    # Handle shortcuts
    if "--db" in args or "db" in args:
        cmd.extend(["-m", "database"])
    elif "--api" in args or "api" in args:
        cmd.extend(["-m", "api"])
    elif "--ui" in args or "ui" in args:
        cmd.extend(["-m", "ui"])
    elif "--e2e" in args or "e2e" in args or "--integration" in args:
        cmd.extend(["-m", "integration"])
    elif "--smoke" in args or "smoke" in args:
        cmd.extend(["-m", "smoke"])

    if "--headed" in args:
        cmd.append("--headed")

    print(f"\nRunning command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)

    # Prompt to view report if user wants
    print(f"\nHTML Report saved at: {REPORT_HTML}")
    return result.returncode

def open_report():
    """Opens HTML test report in default browser."""
    if REPORT_HTML.exists():
        print(f"Opening test report in browser: {REPORT_HTML}")
        webbrowser.open(REPORT_HTML.as_uri())
    else:
        print("No report found yet. Run 'python run.py test' first.")

def print_help():
    print("""
============================================================
 E-Commerce Database Testing - Simple CLI Runner
============================================================

COMMANDS:
  python run.py start                 Start MySQL & FastAPI services
  python run.py stop                  Stop background services
  python run.py status                Check status of MySQL & API
  python run.py init-db               Reset & seed MySQL database

TEST COMMANDS:
  python run.py test                  Run all 75 tests
  python run.py test --db             Run Database & SQL tests
  python run.py test --api            Run REST API tests
  python run.py test --ui             Run UI tests (headless)
  python run.py test --ui --headed    Run UI tests (visible browser window!)
  python run.py test --e2e            Run Integration & End-to-End tests

REPORTING:
  python run.py report                Open interactive HTML report in browser
============================================================
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    action = sys.argv[1].lower()
    extra_args = sys.argv[2:]

    if action in ("start", "up"):
        start_services()
    elif action in ("stop", "down"):
        stop_services()
    elif action in ("status", "info"):
        print_status()
    elif action in ("init-db", "init", "seed"):
        init_db()
    elif action in ("test", "tests"):
        code = run_tests(extra_args)
        sys.exit(code)
    elif action in ("report", "html"):
        open_report()
    elif action in ("help", "-h", "--help"):
        print_help()
    else:
        print(f"Unknown command: '{action}'. Showing help:")
        print_help()
