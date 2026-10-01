import pytest
from database.connection import execute_insert, fetch_one, execute_update, execute_delete
from queries.customer_queries import (
    INSERT_CUSTOMER, SELECT_CUSTOMER_BY_ID, UPDATE_CUSTOMER, DELETE_CUSTOMER
)
from utils.data_generator import TestDataGenerator

@pytest.mark.database
@pytest.mark.regression
class TestCustomerCRUD:
    """Automated CRUD tests for Customer entity in MySQL."""

    def test_create_customer(self):
        """Test CREATE: Insert a new customer and verify database persistence."""
        data = TestDataGenerator.generate_customer_data()
        cust_id = execute_insert(
            INSERT_CUSTOMER,
            (data["first_name"], data["last_name"], data["email"], data["phone"], data["password"], data["status"])
        )
        assert cust_id > 0, "Expected a valid generated customer_id"

        created = fetch_one(SELECT_CUSTOMER_BY_ID, (cust_id,))
        assert created is not None, "Customer record should exist in the database"
        assert created["first_name"] == data["first_name"]
        assert created["last_name"] == data["last_name"]
        assert created["email"] == data["email"]
        assert created["status"] == data["status"]

        # Cleanup
        execute_delete(DELETE_CUSTOMER, (cust_id,))

    def test_read_customer(self, test_customer):
        """Test READ: Query existing customer by ID and verify fields."""
        cust_id = test_customer["customer_id"]
        record = fetch_one(SELECT_CUSTOMER_BY_ID, (cust_id,))
        assert record is not None
        assert record["customer_id"] == cust_id
        assert record["email"] == test_customer["email"]

    def test_update_customer(self, test_customer):
        """Test UPDATE: Modify customer fields and verify changes."""
        cust_id = test_customer["customer_id"]
        updated_first_name = "UpdatedFirstName"
        updated_phone = "+1-555-9999"
        updated_status = "inactive"

        affected = execute_update(
            UPDATE_CUSTOMER,
            (updated_first_name, test_customer["last_name"], updated_phone, updated_status, cust_id)
        )
        assert affected == 1, "Expected 1 row to be updated"

        refreshed = fetch_one(SELECT_CUSTOMER_BY_ID, (cust_id,))
        assert refreshed["first_name"] == updated_first_name
        assert refreshed["phone"] == updated_phone
        assert refreshed["status"] == updated_status

    def test_delete_customer(self):
        """Test DELETE: Remove customer and verify record no longer exists."""
        data = TestDataGenerator.generate_customer_data()
        cust_id = execute_insert(
            INSERT_CUSTOMER,
            (data["first_name"], data["last_name"], data["email"], data["phone"], data["password"], data["status"])
        )
        assert fetch_one(SELECT_CUSTOMER_BY_ID, (cust_id,)) is not None

        affected = execute_delete(DELETE_CUSTOMER, (cust_id,))
        assert affected == 1

        deleted = fetch_one(SELECT_CUSTOMER_BY_ID, (cust_id,))
        assert deleted is None, "Customer should no longer exist after deletion"
