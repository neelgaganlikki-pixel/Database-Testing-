"""Unit and component tests verifying the Database Self-Healing System (Section 29)."""
import pytest
from mysql.connector import Error

from self_healing import (
    ConfidenceEngine,
    DatabaseHealer,
    DatabaseSchemaDiscovery,
    SelfHealingConfig,
    SelfHealingRow,
)


class MockMySQLError(Error):
    def __init__(self, errno, msg):
        super().__init__(msg)
        self.errno = errno


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
        """2. Column renamed: expected 'customerName' or 'customer_name' recovers from 'first_name' / 'first_name'."""
        row_data = {"customerName": "Alice", "email": "alice@test.com"}
        row = SelfHealingRow(row_data, table_name="customers")
        # Test expects 'customer_name'
        assert row["customer_name"] == "Alice"

    def test_03_table_renamed_candidate_discovery(self):
        """3. Table renamed: adapts SELECT from 'customer' to 'customers' using schema metadata."""
        err = MockMySQLError(1146, "Table 'ecommerce_test.customer' doesn't exist")
        # Ensure schema metadata has 'customers' table cached
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
        # Expecting 'total_amount'
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
