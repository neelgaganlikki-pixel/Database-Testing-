"""Self-Healing Reporter, Failure Classifier, and Diagnostic Logger."""
import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from self_healing.config import SelfHealingConfig
from self_healing.security import mask_sensitive_data
from utils.logger import logger


@dataclass
class HealingEvent:
    timestamp: str
    category: str              # 'API' or 'DATABASE'
    test_name: str
    original: str
    candidate: Optional[str]
    status: str                # 'HEALED', 'REJECTED', 'FAILED'
    confidence: float
    reason: str
    failure_classification: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


class FailureClassifier:
    """Classifies failures into standard diagnostic categories."""

    # API Classifications
    API_LOCATOR_MAPPING = "API LOCATOR/MAPPING FAILURE"
    API_CONTRACT = "API CONTRACT FAILURE"
    API_APPLICATION = "API APPLICATION FAILURE"
    AUTHENTICATION = "AUTHENTICATION FAILURE"
    DATA_FAILURE = "DATA FAILURE"
    ENVIRONMENT = "ENVIRONMENT FAILURE"
    ASSERTION_FAILURE = "ASSERTION FAILURE"

    # Database Classifications
    SCHEMA_MAPPING = "SCHEMA/MAPPING FAILURE"
    DB_CONNECTION = "DATABASE CONNECTION FAILURE"
    QUERY_FAILURE = "QUERY FAILURE"
    DB_APPLICATION = "DATABASE APPLICATION FAILURE"

    @classmethod
    def classify_api_failure(cls, expected: str, status_code: Optional[int] = None, details: str = "") -> str:
        det = details.lower()
        if status_code in (401, 403):
            return cls.AUTHENTICATION
        if status_code in (500, 502, 503, 504):
            return cls.API_APPLICATION
        if "connection" in det or "timeout" in det:
            return cls.ENVIRONMENT
        if "expected" in det and "actual" in det:
            return cls.ASSERTION_FAILURE
        return cls.API_CONTRACT

    @classmethod
    def classify_db_failure(cls, original: str, error_msg: str = "") -> str:
        msg = error_msg.lower()
        if "can't connect" in msg or "access denied" in msg or "lost connection" in msg:
            return cls.DB_CONNECTION
        if "syntax" in msg or "you have an error in your sql syntax" in msg:
            return cls.QUERY_FAILURE
        if "unknown column" in msg or "table" in msg and "doesn't exist" in msg:
            return cls.SCHEMA_MAPPING
        if "deadlock" in msg or "lock wait timeout" in msg:
            return cls.DB_APPLICATION
        return cls.SCHEMA_MAPPING


class HealingReporter:
    """Collects and reports all self-healing events across test runs."""

    _lock = threading.RLock()
    _instance: Optional["HealingReporter"] = None

    def __init__(self, report_file: Optional[Path] = None):
        self.report_file = report_file or SelfHealingConfig.REPORT_FILE
        self.events: List[HealingEvent] = []

    @classmethod
    def get_instance(cls) -> "HealingReporter":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def log_api_healing(
        self,
        test_name: str,
        expected: str,
        candidate: str,
        value_type: str,
        confidence: float,
        status: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Logs standard [API-SELF-HEALING] diagnostic block to console and execution log."""
        border = "=" * 40
        log_msg = (
            f"\n{border}\n"
            f"[API-SELF-HEALING]\n\n"
            f"Test:             {test_name}\n"
            f"Expected field:   {expected}\n"
            f"Candidate field:  {candidate}\n"
            f"Value type:       {value_type}\n"
            f"Confidence:       {confidence * 100:.1f}%\n"
            f"Validation:       {'PASSED' if status == 'HEALED' else 'REJECTED'}\n"
            f"Healing Status:   {status}\n"
            f"Reason:           {reason}\n"
            f"{border}\n"
        )
        if status == "HEALED":
            logger.info(log_msg)
        else:
            logger.warning(log_msg)

        event = HealingEvent(
            timestamp=datetime.now().isoformat(),
            category="API",
            test_name=test_name,
            original=expected,
            candidate=candidate,
            status=status,
            confidence=confidence,
            reason=reason,
            failure_classification=FailureClassifier.API_LOCATOR_MAPPING if status != "HEALED" else None,
            context=context or {}
        )
        with self._lock:
            self.events.append(event)

    def log_db_healing(
        self,
        test_name: str,
        expected: str,
        candidate: str,
        data_type: str,
        confidence: float,
        status: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Logs standard [DB-SELF-HEALING] diagnostic block."""
        border = "=" * 40
        log_msg = (
            f"\n{border}\n"
            f"[DB-SELF-HEALING]\n\n"
            f"Test:             {test_name}\n"
            f"Expected column:  {expected}\n"
            f"Candidate column: {candidate}\n"
            f"Data type:        {data_type}\n"
            f"Confidence:       {confidence * 100:.1f}%\n"
            f"Validation:       {'PASSED' if status == 'HEALED' else 'REJECTED'}\n"
            f"Healing Status:   {status}\n"
            f"Reason:           {reason}\n"
            f"{border}\n"
        )
        if status == "HEALED":
            logger.info(log_msg)
        else:
            logger.warning(log_msg)

        event = HealingEvent(
            timestamp=datetime.now().isoformat(),
            category="DATABASE",
            test_name=test_name,
            original=expected,
            candidate=candidate,
            status=status,
            confidence=confidence,
            reason=reason,
            failure_classification=FailureClassifier.SCHEMA_MAPPING if status != "HEALED" else None,
            context=context or {}
        )
        with self._lock:
            self.events.append(event)

    def get_summary_dict(self) -> Dict[str, Any]:
        """Generates statistical summary of healing performance."""
        with self._lock:
            api_events = [e for e in self.events if e.category == "API"]
            db_events = [e for e in self.events if e.category == "DATABASE"]

            api_healed = [e for e in api_events if e.status == "HEALED"]
            api_rejected = [e for e in api_events if e.status in ("REJECTED", "FAILED")]

            db_healed = [e for e in db_events if e.status == "HEALED"]
            db_rejected = [e for e in db_events if e.status in ("REJECTED", "FAILED")]

            high_conf = [asdict(e) for e in self.events if e.confidence >= 0.85]
            low_conf = [asdict(e) for e in self.events if e.confidence < 0.85]

            return {
                "generated_at": datetime.now().isoformat(),
                "total_attempts": len(self.events),
                "successful_healings": len(api_healed) + len(db_healed),
                "rejected_healings": len(api_rejected) + len(db_rejected),
                "api": {
                    "attempts": len(api_events),
                    "healed": len(api_healed),
                    "rejected": len(api_rejected),
                    "events": [asdict(e) for e in api_events]
                },
                "database": {
                    "attempts": len(db_events),
                    "healed": len(db_healed),
                    "rejected": len(db_rejected),
                    "events": [asdict(e) for e in db_events]
                },
                "high_confidence_mappings": high_conf,
                "low_confidence_mappings": low_conf
            }

    def generate_report_file(self) -> Path:
        """Writes JSON report file to disk."""
        summary = self.get_summary_dict()
        sanitized = mask_sensitive_data(summary)
        self.report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.report_file, "w", encoding="utf-8") as f:
            json.dump(sanitized, f, indent=4)
        return self.report_file

    def get_markdown_summary(self) -> str:
        """Returns human-readable text/markdown summary."""
        s = self.get_summary_dict()
        return (
            "\n"
            "============================================================\n"
            "                 SELF-HEALING AUTOMATION SUMMARY             \n"
            "============================================================\n"
            f"Total Healing Attempts:  {s['total_attempts']}\n"
            f"Successfully Healed:     {s['successful_healings']}\n"
            f"Rejected / Failed:       {s['rejected_healings']}\n\n"
            "--- API AUTOMATION ---\n"
            f"Attempts: {s['api']['attempts']} | Healed: {s['api']['healed']} | Rejected: {s['api']['rejected']}\n\n"
            "--- DATABASE TESTING ---\n"
            f"Attempts: {s['database']['attempts']} | Healed: {s['database']['healed']} | Rejected: {s['database']['rejected']}\n"
            "============================================================\n"
        )

    def clear(self) -> None:
        with self._lock:
            self.events.clear()
