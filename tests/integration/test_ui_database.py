import pytest
from pages.customer_page import CustomerPage
from pages.product_page import ProductPage
from database.connection import fetch_one
from queries.customer_queries import SELECT_CUSTOMER_BY_EMAIL
from queries.product_queries import SELECT_PRODUCT_BY_ID
from config.db_config import DBConfig
from utils.data_generator import TestDataGenerator

@pytest.mark.integration
@pytest.mark.ui
@pytest.mark.regression
class TestUIToDatabaseValidation:
    """Integration tests validating UI interactions directly against MySQL database records."""

    def test_ui_customer_registration_to_db_validation(self, page):
        """UI -> DB: Register customer via browser UI and assert database record."""
        cust_page = CustomerPage(page, base_url=DBConfig.API_BASE_URL)
        cust_page.navigate("/")

        cust_data = TestDataGenerator.generate_customer_data()
        cust_page.register(
            first_name=cust_data["first_name"],
            last_name=cust_data["last_name"],
            email=cust_data["email"],
            phone=cust_data["phone"],
            password=cust_data["password"]
        )

        msg = cust_page.get_registration_message()
        assert "successful" in msg.lower()

        # Query MySQL directly to verify record was inserted into customers table
        db_cust = fetch_one(SELECT_CUSTOMER_BY_EMAIL, (cust_data["email"],))
        assert db_cust is not None, f"Database did not find customer with email {cust_data['email']}"
        assert db_cust["first_name"] == cust_data["first_name"]
        assert db_cust["last_name"] == cust_data["last_name"]
        assert db_cust["status"] == "active"

    def test_ui_product_creation_to_db_validation(self, page):
        """UI -> DB: Create product via UI admin form and assert MySQL products table."""
        prod_page = ProductPage(page, base_url=DBConfig.API_BASE_URL)
        prod_page.navigate("/")

        prod_data = TestDataGenerator.generate_product_data(category_id=1)
        prod_page.create_product(
            name=prod_data["product_name"],
            category_id=1,
            price=prod_data["price"],
            stock=prod_data["stock_quantity"]
        )

        msg = prod_page.get_create_product_message()
        assert "created" in msg.lower()

        # Query MySQL directly
        query = "SELECT * FROM products WHERE product_name = %s;"
        db_prod = fetch_one(query, (prod_data["product_name"],))
        assert db_prod is not None
        assert float(db_prod["price"]) == float(prod_data["price"])
        assert db_prod["stock_quantity"] == prod_data["stock_quantity"]

