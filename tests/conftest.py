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
from queries.customer_queries import (
    INSERT_CUSTOMER,
    SELECT_CUSTOMER_BY_ID,
    DELETE_CUSTOMER,
)
from queries.product_queries import (
    INSERT_PRODUCT,
    SELECT_PRODUCT_BY_ID,
    DELETE_PRODUCT,
)
from queries.order_queries import (
    INSERT_ORDER,
    SELECT_ORDER_BY_ID,
    DELETE_ORDER,
)


# ============================================================
# PYTEST COMMAND LINE OPTIONS
# ============================================================

def pytest_addoption(parser):
    """Adds custom command line options to pytest."""

    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run browser tests in headed mode (visible browser window)",
    )


# ============================================================
# DATABASE SETUP
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_suite():
    """
    Session fixture to ensure the database schema and seed data
    are ready before the test suite starts.
    """

    logger.info("Initializing test suite database setup...")

    init_database()

    yield

    logger.info("Test suite execution completed.")


# ============================================================
# DATABASE CONNECTION
# ============================================================

@pytest.fixture(scope="function")
def database_connection():
    """
    Provides a fresh MySQL connection and ensures rollback/closure
    after each test.
    """

    conn = create_connection()

    try:
        yield conn

    finally:
        try:
            if conn.is_connected():
                conn.rollback()
                close_connection(conn)

        except Exception as e:
            logger.warning(
                f"Error closing fixture database connection: {e}"
            )


# ============================================================
# DATABASE CURSOR
# ============================================================

@pytest.fixture(scope="function")
def database_cursor(database_connection):
    """Provides a dictionary cursor for executing queries."""

    cursor = database_connection.cursor(dictionary=True)

    try:
        yield cursor

    finally:
        cursor.close()


# ============================================================
# API CLIENT
# ============================================================

class APIClient:
    """Wrapper around requests.Session for API automation testing."""

    def __init__(self, base_url: str):

        self.base_url = base_url.rstrip("/")

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

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


def ensure_fastapi_running():
    """Ensures the FastAPI backend server is up and responsive before tests run."""
    import time
    import subprocess
    health_url = f"{DBConfig.API_BASE_URL}/health"
    try:
        r = requests.get(health_url, timeout=1.5)
        if r.status_code == 200 and r.json().get("status") == "healthy":
            return
    except Exception:
        pass

    logger.info("FastAPI backend is offline. Starting FastAPI in background...")
    venv_py = ROOT_DIR / "venv" / "Scripts" / "python.exe"
    py_exe = str(venv_py) if venv_py.exists() else sys.executable
    flags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) |
             getattr(subprocess, "DETACHED_PROCESS", 0))
    subprocess.Popen(
        [py_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    for _ in range(20):
        time.sleep(1)
        try:
            r = requests.get(health_url, timeout=1.5)
            if r.status_code == 200 and r.json().get("status") == "healthy":
                logger.info("FastAPI backend started and healthy.")
                return
        except Exception:
            pass
    logger.warning("FastAPI startup check timed out.")


@pytest.fixture(scope="session")
def api_client():
    """Provides an API client configured for the local FastAPI server."""
    ensure_fastapi_running()

    client = APIClient(
        base_url=DBConfig.API_BASE_URL
    )

    return client


# ============================================================
# PLAYWRIGHT BROWSER
# ============================================================

@pytest.fixture(scope="session")
def browser_instance(request):
    """
    Playwright browser instance fixture.

    Supports:
        HEADLESS=true/false
        --headed command-line option

    Jenkins:
        HEADLESS=true

    Local headed execution:
        pytest --headed
    """

    # --------------------------------------------------------
    # Read --headed command-line option
    # --------------------------------------------------------

    cli_headed = request.config.getoption("--headed")

    # --------------------------------------------------------
    # Read HEADLESS environment variable
    # --------------------------------------------------------

    raw_headless = os.getenv("HEADLESS", "true")

    # Convert environment string to Boolean
    env_headless = raw_headless.strip().lower() in (
        "true",
        "1",
        "yes",
        "y",
        "on",
    )

    # --------------------------------------------------------
    # --headed has priority over HEADLESS
    # --------------------------------------------------------

    if cli_headed:
        run_headless = False
    else:
        run_headless = env_headless

    # --------------------------------------------------------
    # Safety validation
    # --------------------------------------------------------

    if not isinstance(run_headless, bool):
        raise TypeError(
            f"Invalid Playwright headless value: "
            f"{run_headless!r}. Expected bool."
        )

    # --------------------------------------------------------
    # Logging
    # --------------------------------------------------------

    mode_str = (
        "HEADLESS (background)"
        if run_headless
        else "HEADED (visible browser window)"
    )

    logger.info(
        f"[UI] Launching Chromium in {mode_str} mode..."
    )

    logger.info(
        f"[UI] HEADLESS environment value: {raw_headless}"
    )

    logger.info(
        f"[UI] Resolved run_headless value: {run_headless}"
    )

    # Ensure backend is up for UI tests
    ensure_fastapi_running()

    # --------------------------------------------------------
    # Launch Playwright
    # --------------------------------------------------------

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=run_headless,
            slow_mo=600 if not run_headless else 0,
        )

        yield browser

        browser.close()


# ============================================================
# PLAYWRIGHT PAGE
# ============================================================

@pytest.fixture(scope="function")
def page(browser_instance, request):
    """
    Playwright page fixture.

    Creates a fresh browser context and page for every test.

    Captures a screenshot automatically when a test fails.
    """

    context = browser_instance.new_context(
        viewport={
            "width": 1280,
            "height": 720,
        }
    )

    page = context.new_page()

    yield page

    # --------------------------------------------------------
    # Screenshot on test failure
    # --------------------------------------------------------

    if (
        hasattr(request.node, "rep_call")
        and request.node.rep_call.failed
    ):

        screenshots_dir = (
            ROOT_DIR
            / "reports"
            / "screenshots"
        )

        screenshots_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Replace invalid Windows filename characters
        safe_test_name = (
            request.node.name
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("*", "_")
            .replace("?", "_")
            .replace('"', "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace("|", "_")
        )

        screenshot_path = (
            screenshots_dir
            / f"{safe_test_name}.png"
        )

        try:

            page.screenshot(
                path=str(screenshot_path),
                full_page=True,
            )

            logger.warning(
                f"UI Test failed! "
                f"Screenshot captured at: "
                f"{screenshot_path}"
            )

        except Exception as e:

            logger.warning(
                f"Unable to capture screenshot: {e}"
            )

    # --------------------------------------------------------
    # Close browser context
    # --------------------------------------------------------

    context.close()


# ============================================================
# PYTEST TEST REPORT HOOK
# ============================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Makes test execution results available to fixtures.

    Used by the page fixture to determine whether a test failed.
    """

    outcome = yield

    rep = outcome.get_result()

    setattr(
        item,
        "rep_" + rep.when,
        rep,
    )


# ============================================================
# TEST CUSTOMER FIXTURE
# ============================================================

@pytest.fixture(scope="function")
def test_customer():
    """
    Creates a temporary customer and cleans it up after the test.
    """

    data = TestDataGenerator.generate_customer_data()

    # --------------------------------------------------------
    # Create customer
    # --------------------------------------------------------

    with DatabaseManager() as db:

        cust_id = db.execute_insert(
            INSERT_CUSTOMER,
            (
                data["first_name"],
                data["last_name"],
                data["email"],
                data["phone"],
                data["password"],
                data["status"],
            ),
        )

        created = db.fetch_one(
            SELECT_CUSTOMER_BY_ID,
            (cust_id,),
        )

    yield created

    # --------------------------------------------------------
    # Cleanup customer
    # --------------------------------------------------------

    with DatabaseManager() as db:

        orders = db.execute_select(
            "SELECT order_id FROM orders "
            "WHERE customer_id = %s;",
            (cust_id,),
        )

        for order in orders:

            order_id = order["order_id"]

            db.execute_delete(
                "DELETE FROM payments "
                "WHERE order_id = %s;",
                (order_id,),
            )

            db.execute_delete(
                "DELETE FROM order_items "
                "WHERE order_id = %s;",
                (order_id,),
            )

        db.execute_delete(
            "DELETE FROM orders "
            "WHERE customer_id = %s;",
            (cust_id,),
        )

        db.execute_delete(
            "DELETE FROM cart "
            "WHERE customer_id = %s;",
            (cust_id,),
        )

        db.execute_delete(
            DELETE_CUSTOMER,
            (cust_id,),
        )


# ============================================================
# TEST PRODUCT FIXTURE
# ============================================================

@pytest.fixture(scope="function")
def test_product():
    """
    Creates a temporary product and cleans it up after the test.
    """

    data = TestDataGenerator.generate_product_data(
        category_id=1
    )

    # --------------------------------------------------------
    # Create product
    # --------------------------------------------------------

    with DatabaseManager() as db:

        prod_id = db.execute_insert(
            INSERT_PRODUCT,
            (
                data["category_id"],
                data["product_name"],
                data["description"],
                data["price"],
                data["stock_quantity"],
                data["status"],
            ),
        )

        created = db.fetch_one(
            SELECT_PRODUCT_BY_ID,
            (prod_id,),
        )

    yield created

    # --------------------------------------------------------
    # Cleanup product
    # --------------------------------------------------------

    with DatabaseManager() as db:

        db.execute_delete(
            "DELETE FROM cart_items "
            "WHERE product_id = %s;",
            (prod_id,),
        )

        db.execute_delete(
            "DELETE FROM order_items "
            "WHERE product_id = %s;",
            (prod_id,),
        )

        db.execute_delete(
            DELETE_PRODUCT,
            (prod_id,),
        )


# ============================================================
# TEST ORDER FIXTURE
# ============================================================

@pytest.fixture(scope="function")
def test_order(test_customer):
    """
    Creates a temporary order and cleans it up after the test.
    """

    order_data = TestDataGenerator.generate_order_data(
        customer_id=test_customer["customer_id"],
        total_amount=199.99,
    )

    # --------------------------------------------------------
    # Create order
    # --------------------------------------------------------

    with DatabaseManager() as db:

        order_id = db.execute_insert(
            INSERT_ORDER,
            (
                order_data["customer_id"],
                order_data["order_number"],
                order_data["total_amount"],
                order_data["status"],
            ),
        )

        created = db.fetch_one(
            SELECT_ORDER_BY_ID,
            (order_id,),
        )

    yield created

    # --------------------------------------------------------
    # Cleanup order
    # --------------------------------------------------------

    with DatabaseManager() as db:

        db.execute_delete(
            "DELETE FROM payments "
            "WHERE order_id = %s;",
            (order_id,),
        )

        db.execute_delete(
            "DELETE FROM order_items "
            "WHERE order_id = %s;",
            (order_id,),
        )

        db.execute_delete(
            DELETE_ORDER,
            (order_id,),
        )