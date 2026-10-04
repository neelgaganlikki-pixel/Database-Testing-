"""
Unified Self-Healing Test Suite.
Consolidates all Self-Healing capabilities into a single comprehensive test case.
Total test count: 1 (bringing the framework's total test count to exactly 76).
"""

import pytest
from mysql.connector import Error

from self_healing import (
    APIHealer,
    ConfidenceEngine,
    DatabaseHealer,
    DatabaseSchemaDiscovery,
    FailureClassifier,
    HealingHistory,
    HealingReporter,
    SelfHealingConfig,
    SelfHealingDict,
    SelfHealingResponse,
    SelfHealingRow,
    mask_sensitive_data,
)


class MockMySQLError(Error):
    """Mock MySQL connector exception with errno."""
    def __init__(self, errno: int, msg: str):
        super().__init__(msg)
        self.errno = errno


@pytest.mark.self_healing
class TestSelfHealing:
    """Unified Self-Healing verification test suite."""

    def setup_method(self):
        SelfHealingConfig.reset_defaults()
        SelfHealingConfig.set_enabled(True)
        SelfHealingConfig.set_api_enabled(True)
        SelfHealingConfig.set_db_enabled(True)

    def teardown_method(self):
        SelfHealingConfig.reset_defaults()

    def test_self_healing_end_to_end_verification(self):
        """
        Consolidated master test validating all self-healing capabilities:
        1. API Field, Nested Attribute & Schema Healing
        2. API Dynamic JSONPath & Versioned Endpoint Healing
        3. Database Column Aliasing & Multi-candidate selection
        4. Database Safe SELECT Query Adaptation (MySQL 1054 & 1146)
        5. Confidence Scoring Engine (Casing, Abbreviations, Type Checks)
        6. Strict Safety & Defect Preservation (Threshold Rejection & Cross-Entity Disallowance)
        7. Security Masking (PII, Passwords, API Keys) & Failure Classification
        """

        # ========================================================
        # 1. API PAYLOAD, NESTED ATTRIBUTE & JSONPATH SELF-HEALING
        # ========================================================
        api_payload = {
            "username": "NeelGagan",
            "customer": {
                "first_name": "Neel",
                "phone_number": "+1-555-0199"
            },
            "result": {
                "user": {
                    "name": "Alice"
                }
            },
            "cust_id": 500
        }
        api_data = SelfHealingDict(api_payload)

        # 1a. Original field exists without overhead
        assert api_data["username"] == "NeelGagan"

        # 1b. Casing/rename healing (userName -> username)
        assert api_data["userName"] == "NeelGagan"

        # 1c. Nested attribute healing (phoneNumber -> phone_number)
        assert api_data["customer"]["phoneNumber"] == "+1-555-0199"

        # 1d. JSONPath structural adaptation ($.data.user.name -> $.result.user.name)
        val, healed_path, conf = APIHealer.heal_jsonpath(api_payload, "$.data.user.name")
        assert val == "Alice"
        assert conf >= 0.85
        assert "result.user.name" in healed_path

        # 1e. Schema contract adaptation
        schema_mappings = APIHealer.heal_schema(
            actual_data={"id": 1, "username": "admin"},
            expected_schema={"userId": int, "userName": str}
        )
        assert schema_mappings["userId"] == "id"
        assert schema_mappings["userName"] == "username"

        # 1f. Endpoint version fallback suggestion
        endpoint_candidate = APIHealer.resolve_endpoint_alternative(
            client_session=None,
            base_url="http://127.0.0.1:8000",
            method="GET",
            endpoint="/api/v1/users",
            known_routes=["/api/v2/users", "/api/v2/orders"]
        )
        assert endpoint_candidate == "/api/v2/users"

        # ========================================================
        # 2. DATABASE ROW, ALIASING & QUERY SELF-HEALING
        # ========================================================
        db_payload = {
            "customer_id": 101,
            "customerName": "Alice",
            "total_amt": 149.50,
            "productName": "Mechanical Keyboard"
        }
        db_row = SelfHealingRow(db_payload, table_name="customers")

        # 2a. Original column access
        assert db_row["customer_id"] == 101

        # 2b. Column rename healing (customer_name -> customerName)
        assert db_row["customer_name"] == "Alice"

        # 2c. Multi-candidate selection (total_amount -> total_amt)
        assert db_row["total_amount"] == 149.50
        assert db_row["product_name"] == "Mechanical Keyboard"

        # 2d. Safe SELECT Query adaptation - Unknown Column (MySQL error 1054)
        col_err = MockMySQLError(1054, "Unknown column 'cust_email' in 'field list'")
        DatabaseSchemaDiscovery._cached_schema = {
            "tables": {"customers": {}},
            "all_columns": {"customer_id", "first_name", "email", "phone"}
        }
        healed_query, col_conf = DatabaseHealer.heal_select_query(
            "SELECT customer_id, cust_email FROM customers WHERE customer_id = 1;", col_err
        )
        assert healed_query is not None
        assert "email" in healed_query
        assert "cust_email" not in healed_query
        assert col_conf >= 0.85

        # 2e. Safe SELECT Query adaptation - Unknown Table (MySQL error 1146)
        tbl_err = MockMySQLError(1146, "Table 'ecommerce_test.customer' doesn't exist")
        DatabaseSchemaDiscovery._cached_schema = {
            "tables": {"customers": {}, "orders": {}},
            "all_columns": {"customer_id", "email"}
        }
        healed_tbl_query, tbl_conf = DatabaseHealer.heal_select_query(
            "SELECT * FROM customer WHERE id = 1;", tbl_err
        )
        assert healed_tbl_query is not None
        assert "FROM customers" in healed_tbl_query
        assert tbl_conf >= 0.85

        # ========================================================
        # 3. CONFIDENCE ENGINE SCORING ALGORITHMS
        # ========================================================
        # 3a. Exact & casing normalization
        assert ConfidenceEngine.calculate_name_similarity("first_name", "first_name") == 1.0
        assert ConfidenceEngine.calculate_name_similarity("firstName", "first_name") >= 0.95
        assert ConfidenceEngine.calculate_name_similarity("FirstName", "first_name") >= 0.95
        assert ConfidenceEngine.calculate_name_similarity("first-name", "first_name") >= 0.95

        # 3b. Synonym and abbreviation scoring
        assert ConfidenceEngine.calculate_name_similarity("cust_id", "customer_id") >= 0.90
        assert ConfidenceEngine.calculate_name_similarity("prod_id", "product_id") >= 0.90

        # 3c. Incompatible data type score penalty
        type_score = ConfidenceEngine.calculate_confidence("uid", "uid_text", expected_val=10, candidate_val="ten")
        assert type_score < 0.70

        # ========================================================
        # 4. STRICT SAFETY & DEFECT PRESERVATION (FAIL-SAFE)
        # ========================================================
        # 4a. Unrelated low-confidence fields MUST raise KeyError (never falsely heal)
        with pytest.raises(KeyError):
            _ = api_data["unrelated_account_balance"]

        with pytest.raises(KeyError):
            _ = db_row["security_pin"]

        # 4b. Cross-entity disallowance (customer_id vs product_id)
        assert ConfidenceEngine.calculate_name_similarity("customer_id", "product_id") <= 0.20

        # 4c. When healing is disabled, strict failures are strictly preserved
        SelfHealingConfig.set_api_enabled(False)
        with pytest.raises(KeyError):
            _ = api_data["userName"]

        SelfHealingConfig.set_db_enabled(False)
        with pytest.raises(KeyError):
            _ = db_row["customer_name"]

        # ========================================================
        # 5. SECURITY PII MASKING & FAILURE CLASSIFICATION
        # ========================================================
        sensitive_data = {
            "customer_id": 42,
            "password": "ClearTextPassword123!",
            "token": "bearer_jwt_sample_token",
            "nested": {"apiKey": "prod_secret_key"}
        }
        masked = mask_sensitive_data(sensitive_data)
        assert masked["customer_id"] == 42
        assert masked["password"] == "******"
        assert masked["token"] == "******"
        assert masked["nested"]["apiKey"] == "******"

        # Failure classifications
        assert FailureClassifier.classify_api_failure("u", status_code=401) == FailureClassifier.AUTHENTICATION
        assert FailureClassifier.classify_api_failure("u", status_code=500) == FailureClassifier.API_APPLICATION
        assert FailureClassifier.classify_db_failure("c", "Can't connect to MySQL server") == FailureClassifier.DB_CONNECTION
        assert FailureClassifier.classify_db_failure("c", "Unknown column 'x' in 'field list'") == FailureClassifier.SCHEMA_MAPPING
