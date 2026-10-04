"""Configuration settings for the Self-Healing Automation Engine."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)

REPORTS_DIR = ROOT_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class SelfHealingConfig:
    """Manages runtime settings for API and Database self-healing."""

    # Master switch
    _ENABLED: bool = os.getenv("SELF_HEALING_ENABLED", "true").strip().lower() in ("true", "1", "yes")

    # Domain switches
    _API_ENABLED: bool = os.getenv("API_SELF_HEALING_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    _DB_ENABLED: bool = os.getenv("DB_SELF_HEALING_ENABLED", "true").strip().lower() in ("true", "1", "yes")

    # Thresholds and limits
    _CONFIDENCE_THRESHOLD: float = float(os.getenv("SELF_HEALING_CONFIDENCE_THRESHOLD", "0.85"))
    _MAX_ATTEMPTS: int = int(os.getenv("SELF_HEALING_MAX_ATTEMPTS", "3"))
    _SAVE_HISTORY: bool = os.getenv("SELF_HEALING_SAVE_HISTORY", "true").strip().lower() in ("true", "1", "yes")
    _LOG_LEVEL: str = os.getenv("SELF_HEALING_LOG_LEVEL", "INFO").strip().upper()

    # File paths
    HISTORY_FILE: Path = REPORTS_DIR / "healing_history.json"
    REPORT_FILE: Path = REPORTS_DIR / "self_healing_report.json"

    @classmethod
    def is_enabled(cls) -> bool:
        return cls._ENABLED

    @classmethod
    def is_api_enabled(cls) -> bool:
        return cls._ENABLED and cls._API_ENABLED

    @classmethod
    def is_db_enabled(cls) -> bool:
        return cls._ENABLED and cls._DB_ENABLED

    @classmethod
    def get_confidence_threshold(cls) -> float:
        return cls._CONFIDENCE_THRESHOLD

    @classmethod
    def get_max_attempts(cls) -> int:
        return cls._MAX_ATTEMPTS

    @classmethod
    def should_save_history(cls) -> bool:
        return cls._SAVE_HISTORY

    @classmethod
    def get_log_level(cls) -> str:
        return cls._LOG_LEVEL

    # Testing overrides
    @classmethod
    def set_enabled(cls, value: bool) -> None:
        cls._ENABLED = value

    @classmethod
    def set_api_enabled(cls, value: bool) -> None:
        cls._API_ENABLED = value

    @classmethod
    def set_db_enabled(cls, value: bool) -> None:
        cls._DB_ENABLED = value

    @classmethod
    def set_confidence_threshold(cls, value: float) -> None:
        cls._CONFIDENCE_THRESHOLD = value

    @classmethod
    def reset_defaults(cls) -> None:
        cls._ENABLED = os.getenv("SELF_HEALING_ENABLED", "true").strip().lower() in ("true", "1", "yes")
        cls._API_ENABLED = os.getenv("API_SELF_HEALING_ENABLED", "true").strip().lower() in ("true", "1", "yes")
        cls._DB_ENABLED = os.getenv("DB_SELF_HEALING_ENABLED", "true").strip().lower() in ("true", "1", "yes")
        cls._CONFIDENCE_THRESHOLD = float(os.getenv("SELF_HEALING_CONFIDENCE_THRESHOLD", "0.85"))
        cls._MAX_ATTEMPTS = int(os.getenv("SELF_HEALING_MAX_ATTEMPTS", "3"))
        cls._SAVE_HISTORY = os.getenv("SELF_HEALING_SAVE_HISTORY", "true").strip().lower() in ("true", "1", "yes")
        cls._LOG_LEVEL = os.getenv("SELF_HEALING_LOG_LEVEL", "INFO").strip().upper()

