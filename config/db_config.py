import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class DBConfig:
    """Database configuration loaded from environment variables."""
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "ecommerce_test")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # API & UI Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    @classmethod
    def is_headless(cls) -> bool:
        """Dynamically re-reads .env to check if headless mode is active."""
        load_dotenv(dotenv_path=env_path, override=True)
        raw_val = os.getenv("HEADLESS", "true").split("#")[0].strip().strip('"').strip("'").lower()
        return raw_val in ("true", "1", "yes")

    @property
    def HEADLESS(self) -> bool:
        return self.is_headless()

    @classmethod
    def get_connection_dict(cls, include_database: bool = True) -> dict:
        """Returns connection dictionary for mysql-connector."""
        config = {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
            "autocommit": False,
        }
        if include_database and cls.DB_NAME:
            config["database"] = cls.DB_NAME
        return config

def get_db_config() -> dict:
    """Helper function to get database connection parameters."""
    return DBConfig.get_connection_dict(include_database=True)

def get_server_config() -> dict:
    """Helper function to connect to MySQL server without selecting database."""
    return DBConfig.get_connection_dict(include_database=False)
