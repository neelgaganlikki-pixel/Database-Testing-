import pytest
from pages.login_page import LoginPage
from config.db_config import DBConfig

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.smoke
class TestUILogin:
    """UI automated tests for Customer Login using Playwright and Page Object Model."""

    def test_customer_successful_login_ui(self, page):
        """Test valid customer login via UI."""
        login_page = LoginPage(page, base_url=DBConfig.API_BASE_URL)
        login_page.navigate("/")

        # Alex Morgan is seeded in database
        login_page.login("alex.morgan@example.com", "hashed_pass_123")

        assert login_page.is_logged_in(), "User should be logged in with badge visible"
        name = login_page.get_logged_in_name()
        assert "Alex Morgan" in name

    def test_customer_invalid_password_login_error_ui(self, page):
        """Test invalid credentials display proper error message."""
        login_page = LoginPage(page, base_url=DBConfig.API_BASE_URL)
        login_page.navigate("/")

        login_page.login("alex.morgan@example.com", "wrong_password_999")
        msg = login_page.get_login_message()
        assert "invalid" in msg.lower() or "error" in msg.lower()

