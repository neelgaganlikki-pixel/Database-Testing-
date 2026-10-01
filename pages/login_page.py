from playwright.sync_api import Page
from pages.base_page import BasePage

class LoginPage(BasePage):
    """Page Object for Customer Login interactions."""

    EMAIL_INPUT = "#login-email"
    PASSWORD_INPUT = "#login-password"
    LOGIN_BUTTON = "#login-btn"
    LOGIN_MESSAGE = "#login-message"
    LOGGED_IN_BADGE = "#user-logged-in-badge"
    LOGGED_USER_NAME = "#logged-user-name"
    LOGOUT_BUTTON = "#logout-btn"

    def __init__(self, page: Page, base_url: str = "http://127.0.0.1:8000"):
        super().__init__(page, base_url)

    def login(self, email: str, password: str) -> None:
        self.fill(self.EMAIL_INPUT, email)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)
        self.page.wait_for_timeout(500)

    def get_login_message(self) -> str:
        self.page.wait_for_selector(self.LOGIN_MESSAGE, state="visible", timeout=5000)
        return self.get_text(self.LOGIN_MESSAGE)

    def is_logged_in(self) -> bool:
        self.page.wait_for_selector(self.LOGGED_IN_BADGE, state="visible", timeout=5000)
        return self.is_visible(self.LOGGED_IN_BADGE)

    def get_logged_in_name(self) -> str:
        return self.get_text(self.LOGGED_USER_NAME)

    def logout(self) -> None:
        self.click(self.LOGOUT_BUTTON)
        self.page.wait_for_timeout(300)
