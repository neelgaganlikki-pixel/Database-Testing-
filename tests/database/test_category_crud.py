import pytest
from database.connection import execute_insert, fetch_one, execute_update, execute_delete
from queries.category_queries import (
    INSERT_CATEGORY, SELECT_CATEGORY_BY_ID, UPDATE_CATEGORY, DELETE_CATEGORY
)
from utils.data_generator import TestDataGenerator

@pytest.mark.database
@pytest.mark.regression
class TestCategoryCRUD:
    """Automated CRUD tests for Category entity in MySQL."""

    def test_create_category(self):
        """Test CREATE: Insert category and check fields."""
        data = TestDataGenerator.generate_category_data()
        cat_id = execute_insert(INSERT_CATEGORY, (data["category_name"], data["description"], data["status"]))
        assert cat_id > 0

        created = fetch_one(SELECT_CATEGORY_BY_ID, (cat_id,))
        assert created is not None
        assert created["category_name"] == data["category_name"]

        # Cleanup
        execute_delete(DELETE_CATEGORY, (cat_id,))

    def test_update_category(self):
        """Test UPDATE: Modify category name and status."""
        data = TestDataGenerator.generate_category_data()
        cat_id = execute_insert(INSERT_CATEGORY, (data["category_name"], data["description"], data["status"]))

        new_name = data["category_name"] + "_Updated"
        affected = execute_update(UPDATE_CATEGORY, (new_name, "Updated Desc", "inactive", cat_id))
        assert affected == 1

        updated = fetch_one(SELECT_CATEGORY_BY_ID, (cat_id,))
        assert updated["category_name"] == new_name
        assert updated["status"] == "inactive"

        # Cleanup
        execute_delete(DELETE_CATEGORY, (cat_id,))

    def test_delete_category(self):
        """Test DELETE: Remove category and assert deletion."""
        data = TestDataGenerator.generate_category_data()
        cat_id = execute_insert(INSERT_CATEGORY, (data["category_name"], data["description"], data["status"]))

        affected = execute_delete(DELETE_CATEGORY, (cat_id,))
        assert affected == 1

        deleted = fetch_one(SELECT_CATEGORY_BY_ID, (cat_id,))
        assert deleted is None
