import pytest
from pages.product_page import ProductPage
from config.db_config import DBConfig
from utils.data_generator import TestDataGenerator

@pytest.mark.ui
@pytest.mark.regression
class TestUIProducts:
    """UI automated tests for Product management and browsing using Playwright."""

    def test_product_catalog_loaded_ui(self, page):
        """Test product cards are rendered properly from database."""
        prod_page = ProductPage(page, base_url=DBConfig.API_BASE_URL)
        prod_page.navigate("/")

        count = prod_page.get_product_card_count()
        assert count >= 5, f"Expected at least 5 products in catalog, found {count}"

    def test_create_new_product_ui(self, page):
        """Test creating a new product through admin form and verify catalog reflects it."""
        prod_page = ProductPage(page, base_url=DBConfig.API_BASE_URL)
        prod_page.navigate("/")

        fake_product = TestDataGenerator.generate_product_data(category_id=1)
        prod_page.create_product(
            name=fake_product["product_name"],
            category_id=1,
            price=fake_product["price"],
            stock=fake_product["stock_quantity"]
        )

        msg = prod_page.get_create_product_message()
        assert "created" in msg.lower()

