import pytest
from database.connection import execute_select
from config.db_config import DBConfig

@pytest.mark.database
@pytest.mark.regression
class TestDatabaseSchema:
    """Automated schema testing querying MySQL INFORMATION_SCHEMA."""

    EXPECTED_TABLES = {
        "customers",
        "categories",
        "products",
        "addresses",
        "cart",
        "cart_items",
        "orders",
        "order_items",
        "payments"
    }

    def _normalize_row(self, row: dict) -> dict:
        """Helper to ensure lowercase keys regardless of MySQL version/driver casing."""
        return {k.lower(): v for k, v in row.items()}

    def test_all_expected_tables_exist(self):
        """Verify all 9 tables exist in the target database schema."""
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s;
        """
        raw_rows = execute_select(query, (DBConfig.DB_NAME,))
        rows = [self._normalize_row(r) for r in raw_rows]
        existing_tables = {row["table_name"].lower() for row in rows}
        missing = self.EXPECTED_TABLES - existing_tables
        assert not missing, f"Missing tables in schema: {missing}"

    def test_customer_table_columns_and_data_types(self):
        """Verify customer table columns and their required data types."""
        query = """
            SELECT column_name, is_nullable, data_type, column_key
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = 'customers';
        """
        raw_rows = execute_select(query, (DBConfig.DB_NAME,))
        rows = [self._normalize_row(r) for r in raw_rows]
        col_map = {row["column_name"].lower(): row for row in rows}

        assert "customer_id" in col_map
        assert col_map["customer_id"]["column_key"] == "PRI"
        assert col_map["customer_id"]["is_nullable"] == "NO"

        assert "email" in col_map
        assert col_map["email"]["column_key"] in ("UNI", "MUL")
        assert col_map["email"]["is_nullable"] == "NO"

        assert "first_name" in col_map
        assert col_map["first_name"]["data_type"] == "varchar"

    def test_primary_keys_across_all_tables(self):
        """Verify every table has a defined PRIMARY KEY constraint."""
        query = """
            SELECT table_name, column_name
            FROM information_schema.key_column_usage
            WHERE table_schema = %s AND constraint_name = 'PRIMARY';
        """
        raw_rows = execute_select(query, (DBConfig.DB_NAME,))
        rows = [self._normalize_row(r) for r in raw_rows]
        pk_tables = {row["table_name"].lower() for row in rows}
        missing_pks = self.EXPECTED_TABLES - pk_tables
        assert not missing_pks, f"Tables missing primary keys: {missing_pks}"

    def test_foreign_key_relationships_defined(self):
        """Verify essential foreign keys are present in information_schema."""
        query = """
            SELECT table_name, column_name, referenced_table_name, referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_schema = %s AND referenced_table_name IS NOT NULL;
        """
        raw_rows = execute_select(query, (DBConfig.DB_NAME,))
        rows = [self._normalize_row(r) for r in raw_rows]
        fk_relationships = {
            (r["table_name"].lower(), r["column_name"].lower(), r["referenced_table_name"].lower()): r
            for r in rows
        }

        # Check critical foreign key relationships
        assert ("products", "category_id", "categories") in fk_relationships
        assert ("addresses", "customer_id", "customers") in fk_relationships
        assert ("cart", "customer_id", "customers") in fk_relationships
        assert ("cart_items", "cart_id", "cart") in fk_relationships
        assert ("cart_items", "product_id", "products") in fk_relationships
        assert ("orders", "customer_id", "customers") in fk_relationships
        assert ("order_items", "order_id", "orders") in fk_relationships
        assert ("order_items", "product_id", "products") in fk_relationships
        assert ("payments", "order_id", "orders") in fk_relationships

