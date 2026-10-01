import logging
import os
import re
from pathlib import Path

# Create logs / reports directory
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = REPORTS_DIR / "execution.log"

SENSITIVE_PATTERNS = [
    (re.compile(r'(password[\'"]?\s*[:=]\s*[\'"])([^\'"]+)([\'"])', re.IGNORECASE), r'\1******\3'),
    (re.compile(r'(pass[\'"]?\s*[:=]\s*[\'"])([^\'"]+)([\'"])', re.IGNORECASE), r'\1******\3'),
    (re.compile(r'(--password=)[^\s]+', re.IGNORECASE), r'\1******'),
]

class SensitiveDataFilter(logging.Filter):
    """Filters out passwords and sensitive credentials from log records."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, repl in SENSITIVE_PATTERNS:
                msg = pattern.sub(repl, msg)
            record.msg = msg
        return True

def get_logger(name: str = "DB_Automation") -> logging.Logger:
    """Configures and returns a logger instance with console and file handlers."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File Handler
        file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveDataFilter())
        logger.addHandler(file_handler)

        # Stream Handler (Console)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(SensitiveDataFilter())
        logger.addHandler(console_handler)

    return logger

# Module-level default logger
logger = get_logger("DB_Testing")
