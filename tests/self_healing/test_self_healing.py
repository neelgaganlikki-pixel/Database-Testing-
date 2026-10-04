"""
Unified Self-Healing Test Suite.
Consolidates all API, Database, Confidence Engine, and Security Self-Healing tests
into a single production-grade test file.

Includes:
1. Unified Master Test Case (End-to-End Self-Healing Pipeline)
2. Detailed Modular Test Cases:
   - TestAPISelfHealing (10 tests)
   - TestDatabaseSelfHealing (10 tests)
   - TestConfidenceAndSecurity (5 tests)
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


# ============================================================
# HELPER MOCKS
# ============================================================

class DummyResponse:
    """Mock requests.Response for API testing."""
    def __init__(self, data: dict, status_code: int = 200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


class MockMySQLError(Error):
    """Mock MySQL connector exception with errno."""
    def __init__(self, errno, msg):
        super().__init__(msg)
        self.errno = errno


# ============================================================
# 1. UNIFIED MASTER TEST CASE
# ============================================================

@pytest.mark.self_healing
class TestUnifiedMasterSelfHealing:
    """
    Unified Master Test Case.
    Executes a comprehensive end-to-end self-healing verification pipeline covering:
    - API payload and JSONPath self-healing
    - Database row and SQL query self-healing
    - Strict safety & low-confidence defect preservation
    - Sensitive data masking and failure classification
    """

    def setup_method(self):
        SelfHealingConfig.reset_defaults()
        SelfHealingConfig.set_enabled(True)
        SelfHealingConfig.set_api_enabled(True)
        SelfHealingConfig.set_db_enabled(True)

    def teardown_method(self):
        SelfHealingConfig.reset_defaults()

    def test_00_unified_master_self_healing_pipeline(self):
        """Unified Master Pipeline: Executes end-to-end self-healing validation."""
        # --- A. API SELF-HEALING ---
        api_payload = {
            "username": "NeelGagan",
            "customer": {"phone_number": "+1-555-0199"},
            "result": {"user": {"name": "Alice"}}
        }
        api_dict = SelfHealingDict(api_payload)

        # 1. API field rename healing
        assert api_dict["userName"] == "NeelGagan"

        # 2. Nested field healing
        assert api_dict["customer"]["phoneNumber"] == "+1-555-0199"

        # 3. JSONPath healing
        val, healed_path, conf = APIHealer.heal_jsonpath(api_payload, "$.data.user.name")
        assert val == "Alice"
        assert conf >= 0.85
        assert "result.user.name" in healed_path

        # --- B. DATABASE SELF-HEALING ---
        db_payload = {"customerName": "Alice", "total_amt": 99.99}
        db_row = SelfHealingRow(db_payload, table_name="customers")

        # 4. Column alias healing
        assert db_row["customer_name"] == "Alice"
        assert db_row["total_amount"] == 99.99

        # 5. Safe SELECT query healing (Unknown Column)
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
        assert col_conf >= 0.85

        # 6. Safe SELECT query healing (Unknown Table)
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

        # --- C. SAFETY & DEFECT PRESERVATION ---
        # 7. Low confidence must reject and fail safely (KeyError)
        with pytest.raises(KeyError):
            _ = api_dict["non_existent_unrelated_field"]

        with pytest.raises(KeyError):
            _ = db_row["unrelated_system_password"]

        # 8. Cross-entity disallowance (customer_id vs product_id)
        entity_sim = ConfidenceEngine.calculate_name_similarity("customer_id", "product_id")
        assert entity_sim <= 0.20

        # --- D. SECURITY MASKING & CLASSIFICATION ---
        # 9. Sensitive data masking
        masked = mask_sensitive_data({"password": "secret", "token": "abc", "user": "neel"})
        assert masked["password"] == "******"
        assert masked["token"] == "******"
        assert masked["user"] == "neel"

        # 10. Failure classification
        assert FailureClassifier.classify_api_failure("u", status_code=401) == FailureClassifier.AUTHENTICATION
        assert FailureClassifier.classify_api_failure("u", status_code=500) == FailureClassifier.API_APPLICATION


# ============================================================
# 2. MODULAR API SELF-HEALING TEST SUITE (10 SCENARIOS)
# ============================================================

@pytest.mark.self_healing
class TestAPISelfHealing:
    """Verifies all 10 API self-healing capabilities defined in the specification."""

    def setup_method(self):
        SelfHealingConfig.reset_defaults()
        SelfHealingConfig.set_enabled(True)
        SelfHealingConfig.set_api_enabled(True)

    def teardown_method(self):
        SelfHealingConfig.reset_defaults()

    def test_01_original_field_exists(self):
        """1. Original field exists: returns cleanly with zero overhead and no healing needed."""
        payload = {"customer_id": 101, "email": "alice@example.com"}
        data = SelfHealingDict(payload)
        assert data["customer_id"] == 101
        assert data["email"] == "alice@example.com"

    def test_02_field_renamed_high_confidence(self):
        """2. Field renamed: recovers when expected 'userName' changes to 'username'."""
        payload = {"username": "NeelGagan", "email": "neel@example.com"}
        data = SelfHealingDict(payload)
        assert data["userName"] == "NeelGagan"

    def test_03_nested_field_changed(self):
        """3. Nested field changed: recovers when a nested object attribute changes case/format."""
        payload = {
            "customer": {
                "first_name": "Neel",
                "phone_number": "+1-555-0199"
            }
        }
        data = SelfHealingDict(payload)
        assert data["customer"]["phoneNumber"] == "+1-555-0199"

    def test_04_jsonpath_changed(self):
        """4. JSONPath changed: adapts from $.data.user.name to $.result.user.name."""
        payload = {
            "result": {
                "user": {
                    "name": "Alice"
                }
            }
        }
        val, healed_path, conf = APIHealer.heal_jsonpath(payload, "$.data.user.name")
        assert val == "Alice"
        assert conf >= 0.85
        assert "result.user.name" in healed_path

    def test_05_schema_changed_diagnostic(self):
        """5. Schema changed: detects schema mapping (userId -> id, userName -> username)."""
        actual_payload = {
            "id": 42,
            "username": "tester",
            "active": True
        }
        expected_schema = {
            "userId": int,
            "userName": str,
            "active": bool
        }
        mappings = APIHealer.heal_schema(actual_payload, expected_schema)
        assert mappings["userId"] == "id"
        assert mappings["userName"] == "username"
        assert mappings["active"] == "active"

    def test_06_multiple_possible_mappings_selects_best(self):
        """6. Multiple possible mappings: selects candidate with highest composite score."""
        payload = {
            "cust_id": 500,
            "customer_identifier": 500,
            "unrelated_field": "test"
        }
        data = SelfHealingDict(payload)
        val = data["customer_id"]
        assert val == 500

    def test_07_high_confidence_mapping_heals(self):
        """7. High-confidence mapping: customerId -> customer_id heals automatically."""
        payload = {"customer_id": 999}
        data = SelfHealingDict(payload)
        assert data["customerId"] == 999

    def test_08_low_confidence_mapping_fails_safely(self):
        """8. Low-confidence mapping: unrelated fields (e.g. total_amount -> password) MUST fail."""
        payload = {"password": "secret", "is_active": True}
        data = SelfHealingDict(payload)
        with pytest.raises(KeyError):
            _ = data["total_amount"]

    def test_09_endpoint_version_change(self):
        """9. Endpoint version change: suggests /api/v2/users when /api/v1/users is requested."""
        known_routes = ["/api/v2/users", "/api/v2/orders", "/api/v2/products"]
        candidate = APIHealer.resolve_endpoint_alternative(
            client_session=None,
            base_url="http://127.0.0.1:8000",
            method="GET",
            endpoint="/api/v1/users",
            known_routes=known_routes
        )
        assert candidate == "/api/v2/users"

    def test_10_healing_disabled_preserves_strict_failure(self):
        """10. Healing disabled: when SELF_HEALING_ENABLED=False, KeyError is raised."""
        SelfHealingConfig.set_api_enabled(False)
        payload = {"username": "Neel"}
        data = SelfHealingDict(payload)
        with pytest.raises(KeyError):
            _ = data["userName"]


# ============================================================
# 3. MODULAR DATABASE SELF-HEALING TEST SUITE (10 SCENARIOS)
# ============================================================

@pytest.mark.self_healing
class TestDatabaseSelfHealing:
    """Verifies all 10 Database self-healing capabilities defined in the specification."""

    def setup_method(self):
        SelfHealingConfig.reset_defaults()
        SelfHealingConfig.set_enabled(True)
        SelfHealingConfig.set_db_enabled(True)

    def teardown_method(self):
        SelfHealingConfig.reset_defaults()

    def test_01_original_column_exists(self):
        """1. Original column exists: retrieves value immediately with zero overhead."""
        row_data = {"customer_id": 1, "first_name": "Neel", "email": "neel@example.com"}
        row = SelfHealingRow(row_data, table_name="customers")
        assert row["customer_id"] == 1
        assert row["first_name"] == "Neel"

    def test_02_column_renamed_in_row(self):
        """2. Column renamed: expected 'customer_name' recovers from 'customerName'."""
        row_data = {"customerName": "Alice", "email": "alice@test.com"}
        row = SelfHealingRow(row_data, table_name="customers")
        assert row["customer_name"] == "Alice"

    def test_03_table_renamed_candidate_discovery(self):
        """3. Table renamed: adapts SELECT from 'customer' to 'customers' using schema metadata."""
        err = MockMySQLError(1146, "Table 'ecommerce_test.customer' doesn't exist")
        DatabaseSchemaDiscovery._cached_schema = {
            "tables": {"customers": {}, "orders": {}, "products": {}},
            "all_columns": {"customer_id", "first_name"}
        }
        healed_query, conf = DatabaseHealer.heal_select_query("SELECT * FROM customer WHERE id = 1;", err)
        assert healed_query is not None
        assert "FROM customers" in healed_query
        assert conf >= 0.85

    def test_04_data_type_mismatch_low_confidence(self):
        """4. Data type changed: string vs integer receives low confidence and will not falsely heal."""
        score = ConfidenceEngine.calculate_confidence(
            expected="quantity",
            candidate="description",
            expected_val=5,
            candidate_val="Five boxes of apples",
            context_score=0.2
        )
        assert score < 0.50

    def test_05_multiple_possible_columns_selects_best(self):
        """5. Multiple possible columns: selects highest-scoring candidate."""
        row_data = {
            "order_number": "ORD-123",
            "total_amt": 99.99,
            "other_val": "X"
        }
        row = SelfHealingRow(row_data, table_name="orders")
        val = row["total_amount"]
        assert val == 99.99

    def test_06_high_confidence_mapping_heals(self):
        """6. High-confidence mapping: 'product_name' -> 'productName' recovers smoothly."""
        row_data = {"productName": "Wireless Mouse", "price": 29.99}
        row = SelfHealingRow(row_data, table_name="products")
        assert row["product_name"] == "Wireless Mouse"

    def test_07_low_confidence_mapping_fails_safely(self):
        """7. Low-confidence mapping: unrelated columns (e.g. 'stock_quantity' -> 'password') MUST raise KeyError."""
        row_data = {"customer_id": 1, "password": "hash"}
        row = SelfHealingRow(row_data, table_name="customers")
        with pytest.raises(KeyError):
            _ = row["stock_quantity"]

    def test_08_relationship_validation_avoids_cross_entity_mapping(self):
        """8. Relationship validation: customer_id does NOT map to product_id despite both being integers."""
        similarity = ConfidenceEngine.calculate_name_similarity("customer_id", "product_id")
        assert similarity <= 0.20, f"Expected cross-entity penalty, got {similarity}"

    def test_09_query_healing_unknown_column(self):
        """9. Query healing: adapts SELECT query when a column in field list was renamed."""
        err = MockMySQLError(1054, "Unknown column 'cust_email' in 'field list'")
        DatabaseSchemaDiscovery._cached_schema = {
            "tables": {"customers": {}},
            "all_columns": {"customer_id", "first_name", "email", "phone"}
        }
        query = "SELECT customer_id, cust_email FROM customers WHERE customer_id = 1;"
        healed_query, conf = DatabaseHealer.heal_select_query(query, err)
        assert healed_query is not None
        assert "email" in healed_query
        assert "cust_email" not in healed_query
        assert conf >= 0.85

    def test_10_healing_disabled_preserves_strict_failure(self):
        """10. Healing disabled: when DB_SELF_HEALING_ENABLED=False, KeyError is raised."""
        SelfHealingConfig.set_db_enabled(False)
        row_data = {"productName": "Keyboard"}
        row = SelfHealingRow(row_data)
        with pytest.raises(KeyError):
            _ = row["product_name"]


# ============================================================
# 4. CONFIDENCE & SECURITY TEST SUITE (5 SCENARIOS)
# ============================================================

@pytest.mark.self_healing
class TestConfidenceAndSecurity:
    """Verifies confidence calculations, historical weights, masking, and failure classification."""

    def test_confidence_exact_and_normalized(self):
        assert ConfidenceEngine.calculate_name_similarity("first_name", "first_name") == 1.0
        assert ConfidenceEngine.calculate_name_similarity("firstName", "first_name") >= 0.95
        assert ConfidenceEngine.calculate_name_similarity("FirstName", "first_name") >= 0.95
        assert ConfidenceEngine.calculate_name_similarity("first-name", "first_name") >= 0.95

    def test_confidence_synonyms_and_abbreviations(self):
        score = ConfidenceEngine.calculate_name_similarity("cust_id", "customer_id")
        assert score >= 0.90
        score2 = ConfidenceEngine.calculate_name_similarity("prod_id", "product_id")
        assert score2 >= 0.90

    def test_confidence_type_penalties(self):
        score = ConfidenceEngine.calculate_confidence("user_id", "user_id_str", expected_val=10, candidate_val="ten")
        assert score < 0.70

    def test_security_sensitive_data_masking(self):
        raw_dict = {
            "user_id": 123,
            "password": "SuperSecretPassword!",
            "auth_token": "bearer_abc_123",
            "nested": {
                "apiKey": "xyz_key",
                "normal": "safe_value"
            }
        }
        masked = mask_sensitive_data(raw_dict)
        assert masked["password"] == "******"
        assert masked["auth_token"] == "******"
        assert masked["nested"]["apiKey"] == "******"
        assert masked["nested"]["normal"] == "safe_value"
        assert masked["user_id"] == 123

    def test_failure_classification(self):
        assert FailureClassifier.classify_api_failure("user", status_code=401) == FailureClassifier.AUTHENTICATION
        assert FailureClassifier.classify_api_failure("user", status_code=500) == FailureClassifier.API_APPLICATION
        assert FailureClassifier.classify_db_failure("col", "Can't connect to MySQL server") == FailureClassifier.DB_CONNECTION
        assert FailureClassifier.classify_db_failure("col", "Unknown column 'xyz' in 'field list'") == FailureClassifier.SCHEMA_MAPPING
