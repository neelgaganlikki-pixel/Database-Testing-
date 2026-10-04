"""Healing History Manager for persisting and reusing validated mappings."""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from self_healing.config import SelfHealingConfig
from self_healing.security import mask_sensitive_data


class HealingHistory:
    """Thread-safe persistent store for successful self-healing mappings."""

    _lock = threading.RLock()
    _instance: Optional["HealingHistory"] = None

    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or SelfHealingConfig.HISTORY_FILE
        self._data: Dict[str, Dict[str, Any]] = {}
        self.load()

    @classmethod
    def get_instance(cls) -> "HealingHistory":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load(self) -> None:
        """Loads historical mappings from disk if file exists."""
        with self._lock:
            if self.history_file.exists():
                try:
                    with open(self.history_file, "r", encoding="utf-8") as f:
                        self._data = json.load(f)
                except Exception:
                    self._data = {}
            else:
                self._data = {}

    def save(self) -> None:
        """Persists historical mappings to disk."""
        if not SelfHealingConfig.should_save_history():
            return
        with self._lock:
            try:
                self.history_file.parent.mkdir(parents=True, exist_ok=True)
                sanitized_data = mask_sensitive_data(self._data)
                with open(self.history_file, "w", encoding="utf-8") as f:
                    json.dump(sanitized_data, f, indent=4)
            except Exception:
                pass

    def get_known_mapping(self, category: str, original: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a previously validated mapping for a given category and original identifier.
        Category is typically 'API' or 'DATABASE'.
        """
        key = f"{category}.{original}"
        with self._lock:
            return self._data.get(key)

    def record_success(
        self,
        category: str,
        original: str,
        healed: str,
        confidence: float,
        test_name: str = "UnknownTest",
        reason: str = "Candidate matched with high confidence"
    ) -> None:
        """Records or increments a successful healing mapping."""
        key = f"{category}.{original}"
        with self._lock:
            existing = self._data.get(key)
            if existing and existing.get("healed") == healed:
                existing["success_count"] = existing.get("success_count", 1) + 1
                existing["last_updated"] = datetime.now().isoformat()
                existing["confidence"] = max(existing.get("confidence", 0.0), confidence)
                if test_name and test_name not in ("unknown", "UnknownTest", "get_current_test_name"):
                    existing["test_name"] = test_name
            else:
                self._data[key] = {
                    "category": category,
                    "original": original,
                    "healed": healed,
                    "confidence": confidence,
                    "success_count": 1,
                    "test_name": test_name,
                    "reason": reason,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
        self.save()

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._data)

    def clear(self) -> None:
        with self._lock:
            self._data = {}
            if self.history_file.exists():
                try:
                    self.history_file.unlink()
                except Exception:
                    pass
