from pathlib import Path
from playwright.sync_api import Page, Locator
from utils.logger import logger

class BasePage:
    """Base Page Object class containing common interactions and helpers."""

    def __init__(self, page: Page, base_url: str = "http://127.0.0.1:8000"):
        self.page = page
        self.base_url = base_url

    def navigate(self, path: str = "/") -> None:
        """Navigates to the specified URL path."""
        url = f"{self.base_url}{path}"
        logger.info(f"Navigating to {url}")
        self.page.goto(url, wait_until="networkidle")

    def wait_for_selector(self, selector: str, timeout: int = 5000) -> Locator:
        return self.page.locator(selector).first

    def click(self, selector: str) -> None:
        logger.debug(f"Clicking on selector: {selector}")
        self.page.locator(selector).click()

    def fill(self, selector: str, value: str) -> None:
        logger.debug(f"Filling selector {selector} with '{value}'")
        self.page.locator(selector).fill(str(value))

    def get_text(self, selector: str) -> str:
        return self.page.locator(selector).inner_text().strip()

    def is_visible(self, selector: str) -> bool:
        return self.page.locator(selector).is_visible()

    def take_screenshot(self, name: str) -> str:
        """Takes a screenshot and stores it under reports/screenshots/."""
        reports_dir = Path(__file__).resolve().parent.parent / "reports" / "screenshots"
        reports_dir.mkdir(parents=True, exist_ok=True)
        file_path = reports_dir / f"{name}.png"
        self.page.screenshot(path=str(file_path))
        logger.info(f"Screenshot saved to: {file_path}")
        return str(file_path)
