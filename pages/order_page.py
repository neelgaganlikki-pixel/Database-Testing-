from playwright.sync_api import Page
from pages.base_page import BasePage

class OrderPage(BasePage):
    """Page Object for Order Confirmation and Payment flow."""

    ORDER_RESULT_CARD = "#order-result-card"
    ORDER_NUMBER_DISPLAY = "#order-number-display"
    ORDER_ID_DISPLAY = "#order-id-display"
    ORDER_TOTAL_DISPLAY = "#order-total-display"
    ORDER_STATUS_DISPLAY = "#order-status-display"
    PAY_BTN = "#pay-btn"
    PAYMENT_MSG = "#payment-message"

    def __init__(self, page: Page, base_url: str = "http://127.0.0.1:8000"):
        super().__init__(page, base_url)

    def is_order_confirmed(self) -> bool:
        self.page.wait_for_selector(self.ORDER_RESULT_CARD, state="visible", timeout=6000)
        return self.is_visible(self.ORDER_RESULT_CARD)

    def get_order_number(self) -> str:
        self.page.wait_for_selector(self.ORDER_NUMBER_DISPLAY, state="visible", timeout=5000)
        return self.get_text(self.ORDER_NUMBER_DISPLAY)

    def get_order_id(self) -> int:
        self.page.wait_for_selector(self.ORDER_ID_DISPLAY, state="visible", timeout=5000)
        return int(self.get_text(self.ORDER_ID_DISPLAY))

    def get_order_total(self) -> float:
        self.page.wait_for_selector(self.ORDER_TOTAL_DISPLAY, state="visible", timeout=5000)
        return float(self.get_text(self.ORDER_TOTAL_DISPLAY).replace("$", "").strip())

    def get_order_status(self) -> str:
        self.page.wait_for_selector(self.ORDER_STATUS_DISPLAY, state="visible", timeout=5000)
        return self.get_text(self.ORDER_STATUS_DISPLAY).strip().lower()

    def pay_order(self) -> None:
        self.page.wait_for_selector(self.PAY_BTN, state="visible", timeout=5000)
        self.click(self.PAY_BTN)
        self.page.wait_for_timeout(800)

    def get_payment_message(self) -> str:
        self.page.wait_for_selector(self.PAYMENT_MSG, state="visible", timeout=5000)
        return self.get_text(self.PAYMENT_MSG)
