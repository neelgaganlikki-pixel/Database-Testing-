import sys
from pathlib import Path
import mysql.connector

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.db_config import get_server_config, get_db_config, DBConfig
from utils.logger import logger

def execute_sql_file(file_path: Path, connection) -> None:
    """Executes a multi-statement SQL file safely."""
    logger.info(f"Executing SQL file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    cursor = connection.cursor()
    try:
        # Split statements or use execute multi
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
        for stmt in statements:
            # Skip empty or comment-only statements
            clean_stmt = "\n".join([line for line in stmt.splitlines() if not line.strip().startswith("--")])
            if clean_stmt.strip():
                cursor.execute(clean_stmt)
        connection.commit()
        logger.info(f"Successfully executed: {file_path.name}")
    except mysql.connector.Error as e:
        logger.error(f"Error executing SQL in {file_path.name}: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()

def init_database() -> None:
    """Creates database, tables, and applies seed data."""
    # 1. Connect without database to create if not exists
    server_cfg = get_server_config()
    conn = mysql.connector.connect(**server_cfg)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DBConfig.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()
    cursor.close()
    conn.close()

    # 2. Connect with database and run schema.sql
    db_cfg = get_db_config()
    db_conn = mysql.connector.connect(**db_cfg)
    schema_file = ROOT_DIR / "database" / "schema.sql"
    execute_sql_file(schema_file, db_conn)

    # 3. Run seed_data.sql
    seed_file = ROOT_DIR / "database" / "seed_data.sql"
    execute_sql_file(seed_file, db_conn)
    db_conn.close()
    logger.info("Database initialized and seeded successfully.")

def cleanup_database() -> None:
    """Cleans up table records."""
    db_cfg = get_db_config()
    db_conn = mysql.connector.connect(**db_cfg)
    cleanup_file = ROOT_DIR / "database" / "cleanup.sql"
    execute_sql_file(cleanup_file, db_conn)
    db_conn.close()
    logger.info("Database cleaned up successfully.")

def reset_database() -> None:
    """Completely resets database and re-runs schema + seed."""
    init_database()
    logger.info("Database reset complete.")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "init"
    if action == "init":
        init_database()
    elif action == "cleanup":
        cleanup_database()
    elif action == "reset":
        reset_database()
    else:
        print(f"Unknown action: {action}. Use 'init', 'cleanup', or 'reset'.")
