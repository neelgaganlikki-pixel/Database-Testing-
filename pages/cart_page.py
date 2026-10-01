from playwright.sync_api import Page
from pages.base_page import BasePage

class CartPage(BasePage):
    """Page Object for Shopping Cart actions."""

    CART_TABLE = "#cart-table"
    CART_ITEMS = "#cart-items tr"
    CART_TOTAL = "#cart-total"
    CHECKOUT_BTN = "#checkout-btn"
    CART_EMPTY_MSG = "#cart-empty-msg"

    def __init__(self, page: Page, base_url: str = "http://127.0.0.1:8000"):
        super().__init__(page, base_url)

    def get_cart_item_count(self) -> int:
        self.page.wait_for_timeout(300)
        return self.page.locator(self.CART_ITEMS).count()

    def get_cart_total(self) -> float:
        self.page.wait_for_selector(self.CART_TOTAL, state="visible", timeout=5000)
        text = self.get_text(self.CART_TOTAL)
        return float(text.replace("$", "").strip())

    def checkout(self) -> None:
        self.page.wait_for_selector(self.CHECKOUT_BTN, state="visible", timeout=5000)
        self.click(self.CHECKOUT_BTN)
        self.page.wait_for_timeout(800)
