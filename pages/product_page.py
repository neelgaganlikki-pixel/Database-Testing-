from playwright.sync_api import Page
from pages.base_page import BasePage

class ProductPage(BasePage):
    """Page Object for Product browsing, creation, and adding to cart."""

    PROD_NAME_INPUT = "#prod-name"
    PROD_CAT_INPUT = "#prod-cat"
    PROD_PRICE_INPUT = "#prod-price"
    PROD_STOCK_INPUT = "#prod-stock"
    CREATE_PROD_BTN = "#create-product-btn"
    CREATE_PROD_MSG = "#product-create-message"
    PRODUCT_LIST = "#product-list"

    def __init__(self, page: Page, base_url: str = "http://127.0.0.1:8000"):
        super().__init__(page, base_url)

    def create_product(self, name: str, category_id: int, price: float, stock: int) -> None:
        self.fill(self.PROD_NAME_INPUT, name)
        self.fill(self.PROD_CAT_INPUT, str(category_id))
        self.fill(self.PROD_PRICE_INPUT, str(price))
        self.fill(self.PROD_STOCK_INPUT, str(stock))
        self.click(self.CREATE_PROD_BTN)
        self.page.wait_for_timeout(500)

    def get_create_product_message(self) -> str:
        self.page.wait_for_selector(self.CREATE_PROD_MSG, state="visible", timeout=5000)
        return self.get_text(self.CREATE_PROD_MSG)

    def add_product_to_cart(self, product_id: int) -> None:
        selector = f"#add-to-cart-btn-{product_id}"
        self.page.wait_for_selector(selector, state="visible", timeout=5000)
        self.click(selector)
        self.page.wait_for_timeout(500)

    def get_product_card_count(self) -> int:
        self.page.wait_for_selector(".product-card", timeout=5000)
        return self.page.locator(".product-card").count()
