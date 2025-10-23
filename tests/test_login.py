# tests/test_login.py
from pathlib import Path
import csv
import pytest
import allure
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.login_page import LoginPage
from pages.base_page import BasePage

def pytest_generate_tests(metafunc):
    """
    Parametrize tests that accept the 'row' arg from data/credentials.csv.
    This runs at collection time (safe to skip module if file missing).
    """
    if "row" in metafunc.fixturenames:
        path = Path(__file__).resolve().parent.parent / "data" / "credentials.csv"
        if not path.exists():
            pytest.skip(
                f"Credentials CSV not found at {path}. "
                f"Run: python tools/create_credentials_csv.py",
                allow_module_level=True,
            )
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        ids = [r.get("case", f"row_{i}") for i, r in enumerate(rows)]
        metafunc.parametrize("row", rows, ids=ids)

@allure.feature("Login Tests (Sauce Demo)")
@pytest.mark.usefixtures("driver")
class TestLogin:

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url, request):
        self.driver = driver
        self.base_page = BasePage(self.driver)
        self.login_page = LoginPage(self.driver)
        self.driver.get(base_url)
        # hand control to the test
        yield
        # 🔽 Always take a screenshot after each test (pass node name for readable file)
        try:
            self.base_page.take_screenshot(request.node.name)
        except Exception:
            # don't block teardown on screenshot errors
            pass

    def test_valid_login(self, base_url):
        self.login_page.login("standard_user", "secret_sauce")
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        assert "inventory.html" in self.driver.current_url
        assert self.driver.title == "Swag Labs"

    def test_invalid_login(self, base_url):
        self.login_page.login("wrong_user", "wrongpass")
        error = self.login_page.get_error_message()
        assert "do not match any user" in error

    def test_empty_credentials(self, base_url):
        self.login_page.login("", "")
        error = self.login_page.get_error_message()
        assert "Username is required" in error

    def test_logout_redirect(self, base_url):
        self.login_page.login("standard_user", "secret_sauce")
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        WebDriverWait(self.driver, 10).until(lambda d: d.find_element("id", "react-burger-menu-btn")).click()
        logout_el = WebDriverWait(self.driver, 10).until(lambda d: d.find_element("id", "logout_sidebar_link"))
        logout_el.click()
        expected = base_url.rstrip("/") + "/"
        WebDriverWait(self.driver, 10).until(EC.url_matches(expected))
        assert self.login_page.is_login_button_displayed()

    @allure.story("CSV-driven login cases")
    def test_login_with_csv(self, base_url, row):
        """
        Data-driven login: each CSV row produces a test case.
        CSV columns: case, username, password, expected
        expected ∈ {success, invalid, empty_username, empty_password, locked}
        """
        username = row.get("username", "")
        password = row.get("password", "")
        expected = row.get("expected", "")

        self.driver.get(base_url)
        self.login_page.login(username, password)

        if expected == "success":
            WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
            assert "inventory.html" in self.driver.current_url
            assert self.driver.title == "Swag Labs"

        elif expected == "invalid":
            msg = self.login_page.get_error_message()
            assert "do not match any user" in msg

        elif expected == "empty_username":
            msg = self.login_page.get_error_message()
            assert "Username is required" in msg

        elif expected == "empty_password":
            msg = self.login_page.get_error_message()
            assert "Password is required" in msg

        elif expected == "locked":
            msg = self.login_page.get_error_message()
            assert "Sorry, this user has been locked out" in msg

        else:
            pytest.fail(f"Unknown expected value in CSV: {expected}")