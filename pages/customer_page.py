from playwright.sync_api import Page
from pages.base_page import BasePage

class CustomerPage(BasePage):
    """Page Object for Customer Registration."""

    FIRSTNAME_INPUT = "#reg-firstname"
    LASTNAME_INPUT = "#reg-lastname"
    EMAIL_INPUT = "#reg-email"
    PHONE_INPUT = "#reg-phone"
    PASSWORD_INPUT = "#reg-password"
    REGISTER_BUTTON = "#register-btn"
    REGISTER_MESSAGE = "#register-message"

    def __init__(self, page: Page, base_url: str = "http://127.0.0.1:8000"):
        super().__init__(page, base_url)

    def register(self, first_name: str, last_name: str, email: str, phone: str, password: str) -> None:
        self.fill(self.FIRSTNAME_INPUT, first_name)
        self.fill(self.LASTNAME_INPUT, last_name)
        self.fill(self.EMAIL_INPUT, email)
        self.fill(self.PHONE_INPUT, phone)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.REGISTER_BUTTON)
        self.page.wait_for_timeout(500)

    def get_registration_message(self) -> str:
        self.page.wait_for_selector(self.REGISTER_MESSAGE, state="visible", timeout=5000)
        return self.get_text(self.REGISTER_MESSAGE)
