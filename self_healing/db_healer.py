"""Database Self-Healing Engine: Schema discovery, column healing, table mapping, and safe query adaptation."""
import inspect
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import mysql.connector
from mysql.connector import Error

from config.db_config import get_db_config
from self_healing.config import SelfHealingConfig
from self_healing.confidence import ConfidenceEngine
from self_healing.history import HealingHistory
from self_healing.reporter import FailureClassifier, HealingReporter
from utils.logger import logger


def get_current_test_name() -> str:
    """Introspects call stack to determine the active test function name."""
    for frame in inspect.stack():
        func_name = frame.function
        if func_name != "get_current_test_name" and func_name.startswith("test_"):
            return func_name
    return "DB_Test"


class DatabaseSchemaDiscovery:
    """Discovers and caches MySQL schema metadata (tables, columns, types, keys)."""

    _cached_schema: Optional[Dict[str, Dict[str, Any]]] = None

    @classmethod
    def get_schema_metadata(cls, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Inspects INFORMATION_SCHEMA using read-only queries and returns cached metadata:
        {
            "tables": { "customers": { "columns": {"customer_id": "int", ...}, "pk": "customer_id", "fks": [] } }
        }
        """
        if cls._cached_schema and not force_refresh:
            return cls._cached_schema

        metadata: Dict[str, Any] = {"tables": {}, "all_columns": set()}
        cfg = get_db_config()
        db_name = cfg.get("database", "ecommerce_test")

        try:
            conn = mysql.connector.connect(**cfg)
            cursor = conn.cursor(dictionary=True)

            # Discover columns and data types
            query = """
                SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_KEY, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
            """
            cursor.execute(query, (db_name,))
            rows = cursor.fetchall()

            for r in rows:
                tbl = r["TABLE_NAME"]
                col = r["COLUMN_NAME"]
                dtype = r["DATA_TYPE"]
                key = r["COLUMN_KEY"]

                if tbl not in metadata["tables"]:
                    metadata["tables"][tbl] = {
                        "columns": {},
                        "primary_keys": [],
                        "foreign_keys": []
                    }

                metadata["tables"][tbl]["columns"][col] = {
                    "data_type": dtype,
                    "is_primary": (key == "PRI")
                }
                metadata["all_columns"].add(col)
                if key == "PRI":
                    metadata["tables"][tbl]["primary_keys"].append(col)

            cursor.close()
            conn.close()
            cls._cached_schema = metadata
            logger.debug(f"Schema discovery completed for database '{db_name}'.")
        except Exception as e:
            logger.warning(f"Unable to discover database schema metadata: {e}")
            cls._cached_schema = {"tables": {}, "all_columns": set()}

        return cls._cached_schema


class SelfHealingRow(dict):
    """
    Intelligent Dictionary proxy for SQL query result rows.
    Preserves normal dictionary operations, but upon missing column access,
    evaluates column candidates from the row and schema metadata.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None, table_name: Optional[str] = None):
        super().__init__()
        self._table_name = table_name
        if data:
            self.update(data)

    def __getitem__(self, key: Any) -> Any:
        if key in self:
            return super().__getitem__(key)

        if not SelfHealingConfig.is_db_enabled():
            raise KeyError(key)

        expected_col = str(key)
        test_name = get_current_test_name()
        history = HealingHistory.get_instance()
        reporter = HealingReporter.get_instance()

        # Step 1: Check historical mapping
        known = history.get_known_mapping("DATABASE", expected_col)
        if known and known.get("healed") in self:
            candidate_col = known["healed"]
            confidence = known.get("confidence", 0.95)
            val = super().__getitem__(candidate_col)
            reporter.log_db_healing(
                test_name=test_name,
                expected=expected_col,
                candidate=candidate_col,
                data_type=type(val).__name__,
                confidence=confidence,
                status="HEALED",
                reason="Restored from previously validated database healing history",
                context={"table": self._table_name, "historical": True}
            )
            history.record_success("DATABASE", expected_col, candidate_col, confidence, test_name)
            return val

        # Step 2: Search candidate columns in this row
        candidates = list(self.keys())
        if not candidates:
            raise KeyError(key)

        best_cand: Optional[str] = None
        best_conf: float = 0.0

        for cand in candidates:
            cand_val = super().__getitem__(cand)
            score = ConfidenceEngine.calculate_confidence(
                expected=expected_col,
                candidate=str(cand),
                expected_val=None,
                candidate_val=cand_val,
                context_score=0.75
            )
            if score > best_conf:
                best_conf = score
                best_cand = cand

        threshold = SelfHealingConfig.get_confidence_threshold()

        # Step 3: Healing validation gate
        if best_cand and best_conf >= threshold:
            val = super().__getitem__(best_cand)
            reporter.log_db_healing(
                test_name=test_name,
                expected=expected_col,
                candidate=best_cand,
                data_type=type(val).__name__,
                confidence=best_conf,
                status="HEALED",
                reason=f"Candidate column validated above confidence threshold ({best_conf:.2f} >= {threshold:.2f})",
                context={"table": self._table_name}
            )
            history.record_success(
                category="DATABASE",
                original=expected_col,
                healed=best_cand,
                confidence=best_conf,
                test_name=test_name,
                reason="Column renamed candidate validated"
            )
            return val

        # Step 4: Reject candidate and fail safely without masking defects
        reporter.log_db_healing(
            test_name=test_name,
            expected=expected_col,
            candidate=best_cand or "None",
            data_type=type(super().__getitem__(best_cand)).__name__ if best_cand else "Unknown",
            confidence=best_conf,
            status="REJECTED",
            reason=f"Confidence {best_conf:.2f} is below required threshold {threshold:.2f}"
        )
        raise KeyError(key)


class DatabaseHealer:
    """Static and instance methods for database schema, column, table, and query healing."""

    @staticmethod
    def is_read_only_query(query: str) -> bool:
        """Verifies that a query is strictly read-only (SELECT / SHOW / DESCRIBE / EXPLAIN)."""
        stripped = query.strip().upper()
        read_only_verbs = ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")
        return any(stripped.startswith(verb) for verb in read_only_verbs)

    @classmethod
    def heal_select_query(cls, query: str, error: Error) -> Tuple[Optional[str], float]:
        """
        Attempts to heal a failed SELECT query if caused by renamed columns or tables (Errors 1054 or 1146).
        Safety: NEVER operates on non-SELECT statements.
        Returns (healed_query, confidence).
        """
        if not cls.is_read_only_query(query) or not SelfHealingConfig.is_db_enabled():
            return None, 0.0

        err_code = getattr(error, "errno", None)
        err_msg = str(error)
        test_name = get_current_test_name()
        reporter = HealingReporter.get_instance()
        schema = DatabaseSchemaDiscovery.get_schema_metadata()
        threshold = SelfHealingConfig.get_confidence_threshold()

        # Case A: MySQL Error 1054: Unknown column 'col_name' in 'field list' / 'where clause'
        if err_code == 1054 or "unknown column" in err_msg.lower():
            match = re.search(r"unknown column ['`]([^'`]+)['`]", err_msg, re.IGNORECASE)
            if match:
                missing_col = match.group(1)
                all_cols = schema.get("all_columns", set())

                best_cand = None
                best_score = 0.0
                for cand in all_cols:
                    score = ConfidenceEngine.calculate_name_similarity(missing_col, cand)
                    if score > best_score:
                        best_score = score
                        best_cand = cand

                if best_cand and best_score >= threshold:
                    # Construct healed query with word boundary replacement
                    healed_query = re.sub(rf"\b{re.escape(missing_col)}\b", best_cand, query)
                    reporter.log_db_healing(
                        test_name=test_name,
                        expected=missing_col,
                        candidate=best_cand,
                        data_type="COLUMN",
                        confidence=best_score,
                        status="HEALED",
                        reason=f"Query adapted by replacing unknown column '{missing_col}' with '{best_cand}'",
                        context={"original_query": query, "healed_query": healed_query}
                    )
                    return healed_query, best_score

        # Case B: MySQL Error 1146: Table 'db.table_name' doesn't exist
        elif err_code == 1146 or "doesn't exist" in err_msg.lower():
            match = re.search(r"table ['`].*\.([^'`]+)['`]", err_msg, re.IGNORECASE)
            if match:
                missing_table = match.group(1)
                known_tables = list(schema.get("tables", {}).keys())

                best_tbl = None
                best_score = 0.0
                for cand_tbl in known_tables:
                    score = ConfidenceEngine.calculate_name_similarity(missing_table, cand_tbl)
                    if score > best_score:
                        best_score = score
                        best_tbl = cand_tbl

                if best_tbl and best_score >= threshold:
                    healed_query = re.sub(rf"\b{re.escape(missing_table)}\b", best_tbl, query)
                    reporter.log_db_healing(
                        test_name=test_name,
                        expected=missing_table,
                        candidate=best_tbl,
                        data_type="TABLE",
                        confidence=best_score,
                        status="HEALED",
                        reason=f"Query adapted by replacing table '{missing_table}' with candidate '{best_tbl}'",
                        context={"original_query": query, "healed_query": healed_query}
                    )
                    return healed_query, best_score

        # If not healable, report rejected
        reporter.log_db_healing(
            test_name=test_name,
            expected=query[:40] + "...",
            candidate="None",
            data_type="SQL",
            confidence=0.0,
            status="REJECTED",
            reason=f"Database query error could not be healed: {err_msg}"
        )
        return None, 0.0
