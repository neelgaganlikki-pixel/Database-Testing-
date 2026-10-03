"""Verification and self-healing startup script for MySQL / MariaDB."""
import os
import sys
import time
import subprocess
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.db_config import DBConfig, get_server_config
from utils.logger import logger

def is_mysql_online() -> bool:
    """Checks if MySQL accepts connections."""
    try:
        import mysql.connector
        cfg = get_server_config()
        conn = mysql.connector.connect(**cfg)
        connected = conn.is_connected()
        conn.close()
        return connected
    except Exception:
        return False

def start_portable_mysqld() -> bool:
    """Locates and starts portable MariaDB if available."""
    candidates = [
        ROOT_DIR / "mariadb" / "bin" / "mysqld.exe",
        Path(r"D:\Automation Testing\DataBase Testing\mariadb\bin\mysqld.exe"),
    ]
    for mysqld in candidates:
        if mysqld.exists():
            datadir = mysqld.parent.parent / "data"
            logger.info(f"Auto-starting portable MariaDB server from: {mysqld}")
            flags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) |
                     getattr(subprocess, "DETACHED_PROCESS", 0))
            subprocess.Popen(
                [str(mysqld), f"--datadir={datadir}", "--port=3306", "--console"],
                creationflags=flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
    return False

def main():
    if not is_mysql_online():
        logger.warning(f"MySQL on {DBConfig.DB_HOST}:{DBConfig.DB_PORT} is OFFLINE.")
        if start_portable_mysqld():
            logger.info("Waiting for MySQL server to initialize...")
            for _ in range(15):
                time.sleep(1)
                if is_mysql_online():
                    logger.info("MySQL server successfully started!")
                    break

    if is_mysql_online():
        print(f"MySQL Server Online\nHost: {DBConfig.DB_HOST}\nPort: {DBConfig.DB_PORT}")
        sys.exit(0)
    else:
        print(f"ERROR: Could not connect to MySQL server on {DBConfig.DB_HOST}:{DBConfig.DB_PORT}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
