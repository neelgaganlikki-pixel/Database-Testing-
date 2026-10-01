import pytest
from pages.login_page import LoginPage
from pages.product_page import ProductPage
from pages.cart_page import CartPage
from pages.order_page import OrderPage
from config.db_config import DBConfig

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.smoke
class TestUIOrderWorkflow:
    """UI automated tests for End-to-End Shopping Cart, Checkout, and Payment flow."""

    def test_add_product_to_cart_ui(self, page):
        """Test user login and adding product to cart updates cart summary."""
        login_page = LoginPage(page, base_url=DBConfig.API_BASE_URL)
        prod_page = ProductPage(page, base_url=DBConfig.API_BASE_URL)
        cart_page = CartPage(page, base_url=DBConfig.API_BASE_URL)

        login_page.navigate("/")
        login_page.login("alex.morgan@example.com", "hashed_pass_123")

        # Add product 1 to cart
        prod_page.add_product_to_cart(product_id=1)

        item_count = cart_page.get_cart_item_count()
        assert item_count >= 1, "Cart table should contain at least 1 item"
        total = cart_page.get_cart_total()
        assert total > 0.0

    def test_place_order_and_pay_ui(self, page):
        """Test full checkout flow: login -> cart -> place order -> pay."""
        login_page = LoginPage(page, base_url=DBConfig.API_BASE_URL)
        prod_page = ProductPage(page, base_url=DBConfig.API_BASE_URL)
        cart_page = CartPage(page, base_url=DBConfig.API_BASE_URL)
        order_page = OrderPage(page, base_url=DBConfig.API_BASE_URL)

        login_page.navigate("/")
        login_page.login("jordan.lee@example.com", "hashed_pass_456")

        # Add product to cart
        prod_page.add_product_to_cart(product_id=3)

        # Checkout
        cart_page.checkout()

        # Verify order confirmation
        assert order_page.is_order_confirmed()
        order_num = order_page.get_order_number()
        assert "ORD-" in order_num

        # Pay
        order_page.pay_order()
        pay_msg = order_page.get_payment_message()
        assert "processed" in pay_msg.lower() or "ref:" in pay_msg.lower()
        assert order_page.get_order_status() == "confirmed"

