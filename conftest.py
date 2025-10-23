import os
import pytest
import tempfile
import uuid
import shutil
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
import time
import shutil as sh

# ----------------------------------------------------------
#  DEFAULT BROWSER – changed to EDGE
# ----------------------------------------------------------
DEFAULT_BROWSER = os.getenv("DEFAULT_BROWSER", "edge").lower()   # ← NEW

def pytest_addoption(parser):
    """Add command-line options for browser selection"""
    parser.addoption(
        "--browser",
        action="store",
        default=DEFAULT_BROWSER,                           # ← CHANGED
        help=f"Browser to run tests: chrome, edge (default: {DEFAULT_BROWSER})"
    )

# ---------- helpers ----------
def _get_edge_driver_path():
    """
    Look for msedgedriver.exe under the PROJECT ROOT (this conftest.py's directory),
    and a few common locations. This matches where you placed the file:
    <project>/drivers/edgedriver_win64/msedgedriver.exe
    """
    # ✅ Point to the project root (where this conftest.py lives)
    project_root = Path(__file__).parent

    possible_paths = [
        project_root / "drivers" / "edgedriver_win64" / "msedgedriver.exe",
        project_root / "drivers" / "msedgedriver.exe",
        Path("C:/WebDrivers/msedgedriver.exe"),
        Path.home() / "WebDrivers" / "msedgedriver.exe",
        Path("msedgedriver.exe"),
    ]

    path_driver = sh.which("msedgedriver")
    if path_driver:
        print(f"✓ Found Edge driver in PATH: {path_driver}")
        return path_driver

    for path in possible_paths:
        if path.exists() and path.is_file():
            print(f"✓ Found Edge driver at: {path}")
            return str(path)

    print("✗ Edge driver not found. Searched locations:")
    for path in possible_paths:
        status = "EXISTS" if path.exists() else "NOT FOUND"
        print(f"  [{status}] {path}")
    return None

def _build_chrome(headless: bool) -> webdriver.Chrome:
    options = ChromeOptions()
    profile = tempfile.mkdtemp(prefix=f"chrome_{uuid.uuid4().hex}_")
    options.add_argument(f"--user-data-dir={profile}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    if headless:
        options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    # attach profile so the fixture can clean it up after the test
    driver._tmp_profile_dir = profile
    return driver

def _build_edge(headless: bool) -> webdriver.Edge:
    options = EdgeOptions()
    profile = tempfile.mkdtemp(prefix=f"edge_{uuid.uuid4().hex}_")
    options.add_argument(f"--user-data-dir={profile}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    if headless:
        options.add_argument("--headless=new")

    driver_path = _get_edge_driver_path()
    if driver_path:
        print(f"→ Using Edge driver from: {driver_path}")
        service = EdgeService(executable_path=driver_path)
        driver = webdriver.Edge(service=service, options=options)
    else:
        project_root = Path(__file__).parent
        error_msg = f"""
╔════════════════════════════════════════════════════════════════╗
║                   Edge Driver Not Found!                       ║
╚════════════════════════════════════════════════════════════════╝
The driver should be at:
  {project_root / 'drivers' / 'edgedriver_win64' / 'msedgedriver.exe'}
If the file exists but wasn't found, try:
1. Move msedgedriver.exe directly to:
   {project_root / 'drivers' / 'msedgedriver.exe'}
2. Or place it on PATH and retry.
Your Edge version: (example) 141.0.3537.92
Driver download: https://msedgedriver.azureedge.net/141.0.3537.92/edgedriver_win64.zip
        """
        raise FileNotFoundError(error_msg)

    # attach profile so the fixture can clean it up after the test
    driver._tmp_profile_dir = profile
    return driver

# ---------- fixtures ----------
@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("BASE_URL", "https://www.saucedemo.com")

@pytest.fixture(scope="session")
def headless() -> bool:
    return os.getenv("HEADLESS", "false").lower() in {"1", "true", "yes", "on"}

@pytest.fixture(scope="function")
def driver(request, headless: bool):
    """
    Create a fresh browser per test and ensure full teardown after each test.
    This prevents multiple browsers from stacking up.
    """
    browser = request.config.getoption("--browser").lower()
    if browser == "chrome":
        driver_instance = _build_chrome(headless=headless)
    elif browser == "edge":
        driver_instance = _build_edge(headless=headless)
    else:
        raise ValueError(f"Unsupported browser: {browser}. Supported browsers: chrome, edge")

    driver_instance.implicitly_wait(2)

    yield driver_instance

    # ✅ Per-test teardown
    try:
        driver_instance.quit()
    except Exception as e:
        print(f"Error quitting {browser} driver: {e}")
    finally:
        profile_dir = getattr(driver_instance, "_tmp_profile_dir", None)
        if profile_dir:
            shutil.rmtree(profile_dir, ignore_errors=True)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_setup(item):
    print(f"\n=== Executing test: {item.nodeid} ===")
    time.sleep(0.5)
    yield

@pytest.fixture(autouse=True)
def visual_pause():
    yield
    time.sleep(0.5)