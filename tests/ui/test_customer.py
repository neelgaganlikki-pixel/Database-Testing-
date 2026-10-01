import pytest
from pages.customer_page import CustomerPage
from config.db_config import DBConfig
from utils.data_generator import TestDataGenerator

@pytest.mark.ui
@pytest.mark.regression
class TestUICustomerRegistration:
    """UI automated tests for Customer Registration flow using Playwright."""

    def test_customer_registration_success_ui(self, page):
        """Test customer registration via UI form."""
        customer_page = CustomerPage(page, base_url=DBConfig.API_BASE_URL)
        customer_page.navigate("/")

        cust_data = TestDataGenerator.generate_customer_data()
        customer_page.register(
            first_name=cust_data["first_name"],
            last_name=cust_data["last_name"],
            email=cust_data["email"],
            phone=cust_data["phone"],
            password=cust_data["password"]
        )

        msg = customer_page.get_registration_message()
        assert "successful" in msg.lower() or "customer id" in msg.lower()

    def test_customer_registration_duplicate_email_ui(self, page):
        """Negative Test: UI displays error message when registering with an existing email."""
        customer_page = CustomerPage(page, base_url=DBConfig.API_BASE_URL)
        customer_page.navigate("/")

        # Use existing seeded email
        customer_page.register(
            first_name="Test",
            last_name="Duplicate",
            email="alex.morgan@example.com",
            phone="+1-555-0101",
            password="pass"
        )

        msg = customer_page.get_registration_message()
        assert "already exists" in msg.lower() or "conflict" in msg.lower() or "failed" in msg.lower()

