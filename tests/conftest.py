import os
import sys
from pathlib import Path
import pytest
import requests
from playwright.sync_api import sync_playwright

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.db_config import DBConfig, get_db_config
from database.connection import DatabaseManager, create_connection, close_connection
from database.db_setup import init_database
from utils.data_generator import TestDataGenerator
from utils.logger import logger
from queries.customer_queries import INSERT_CUSTOMER, SELECT_CUSTOMER_BY_ID, DELETE_CUSTOMER
from queries.product_queries import INSERT_PRODUCT, SELECT_PRODUCT_BY_ID, DELETE_PRODUCT
from queries.order_queries import INSERT_ORDER, SELECT_ORDER_BY_ID, DELETE_ORDER

@pytest.fixture(scope="session", autouse=True)
def setup_test_suite():
    """Session fixture to ensure the database schema and seed data are ready."""
    logger.info("Initializing test suite database setup...")
    init_database()
    yield
    logger.info("Test suite execution completed.")

@pytest.fixture(scope="function")
def database_connection():
    """Provides a fresh MySQL connection and ensures rollback/closure after test."""
    conn = create_connection()
    try:
        yield conn
    finally:
        try:
            if conn.is_connected():
                conn.rollback()
                close_connection(conn)
        except Exception as e:
            logger.warning(f"Error closing fixture database connection: {e}")

@pytest.fixture(scope="function")
def database_cursor(database_connection):
    """Provides a dictionary cursor for executing queries."""
    cursor = database_connection.cursor(dictionary=True)
    try:
        yield cursor
    finally:
        cursor.close()

class APIClient:
    """Wrapper around requests.Session for API automation testing."""
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

    def get(self, endpoint: str, **kwargs):
        url = f"{self.base_url}{endpoint}"
        logger.info(f"API GET: {url}")
        return self.session.get(url, **kwargs)

    def post(self, endpoint: str, **kwargs):
        url = f"{self.base_url}{endpoint}"
        logger.info(f"API POST: {url}")
        return self.session.post(url, **kwargs)

    def put(self, endpoint: str, **kwargs):
        url = f"{self.base_url}{endpoint}"
        logger.info(f"API PUT: {url}")
        return self.session.put(url, **kwargs)

    def delete(self, endpoint: str, **kwargs):
        url = f"{self.base_url}{endpoint}"
        logger.info(f"API DELETE: {url}")
        return self.session.delete(url, **kwargs)

@pytest.fixture(scope="session")
def api_client():
    """Provides an API client configured for the local FastAPI server."""
    client = APIClient(base_url=DBConfig.API_BASE_URL)
    return client

@pytest.fixture(scope="session")
def browser_instance():
    """Playwright browser instance fixture."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=DBConfig.HEADLESS)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser_instance, request):
    """Playwright page fixture with screenshot capture on failure."""
    context = browser_instance.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    yield page

    # Screenshot on test failure
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        screenshots_dir = ROOT_DIR / "reports" / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshots_dir / f"{request.node.name}.png"
        page.screenshot(path=str(screenshot_path))
        logger.warning(f"UI Test failed! Screenshot captured at: {screenshot_path}")

    context.close()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

@pytest.fixture(scope="function")
def test_customer():
    """Fixture creating a temporary customer and cleaning it up after the test."""
    data = TestDataGenerator.generate_customer_data()
    with DatabaseManager() as db:
        cust_id = db.execute_insert(
            INSERT_CUSTOMER,
            (data["first_name"], data["last_name"], data["email"], data["phone"], data["password"], data["status"])
        )
        created = db.fetch_one(SELECT_CUSTOMER_BY_ID, (cust_id,))

    yield created

    # Safe cascade cleanup
    with DatabaseManager() as db:
        orders = db.execute_select("SELECT order_id FROM orders WHERE customer_id = %s;", (cust_id,))
        for o in orders:
            oid = o["order_id"]
            db.execute_delete("DELETE FROM payments WHERE order_id = %s;", (oid,))
            db.execute_delete("DELETE FROM order_items WHERE order_id = %s;", (oid,))
        db.execute_delete("DELETE FROM orders WHERE customer_id = %s;", (cust_id,))
        db.execute_delete("DELETE FROM cart WHERE customer_id = %s;", (cust_id,))
        db.execute_delete(DELETE_CUSTOMER, (cust_id,))

@pytest.fixture(scope="function")
def test_product():
    """Fixture creating a temporary product and cleaning it up after the test."""
    data = TestDataGenerator.generate_product_data(category_id=1)
    with DatabaseManager() as db:
        prod_id = db.execute_insert(
            INSERT_PRODUCT,
            (data["category_id"], data["product_name"], data["description"], data["price"], data["stock_quantity"], data["status"])
        )
        created = db.fetch_one(SELECT_PRODUCT_BY_ID, (prod_id,))

    yield created

    # Safe cleanup
    with DatabaseManager() as db:
        db.execute_delete("DELETE FROM cart_items WHERE product_id = %s;", (prod_id,))
        db.execute_delete("DELETE FROM order_items WHERE product_id = %s;", (prod_id,))
        db.execute_delete(DELETE_PRODUCT, (prod_id,))

@pytest.fixture(scope="function")
def test_order(test_customer):
    """Fixture creating a temporary order and cleaning it up after the test."""
    order_data = TestDataGenerator.generate_order_data(customer_id=test_customer["customer_id"], total_amount=199.99)
    with DatabaseManager() as db:
        order_id = db.execute_insert(
            INSERT_ORDER,
            (order_data["customer_id"], order_data["order_number"], order_data["total_amount"], order_data["status"])
        )
        created = db.fetch_one(SELECT_ORDER_BY_ID, (order_id,))

    yield created

    # Safe cleanup
    with DatabaseManager() as db:
        db.execute_delete("DELETE FROM payments WHERE order_id = %s;", (order_id,))
        db.execute_delete("DELETE FROM order_items WHERE order_id = %s;", (order_id,))
        db.execute_delete(DELETE_ORDER, (order_id,))

