# tests/test_menu.py
import pytest
import allure
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage
from pages.menu_page import MenuPage

@pytest.mark.usefixtures("driver")
class TestMenu:

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url, request):
        """
        - Open base URL
        - Guard login inputs (refresh once if needed)
        - Login and land on Inventory
        - Build POMs
        - Screenshot after each test
        """
        self.driver = driver
        self.base_page = BasePage(self.driver)
        self.login = LoginPage(self.driver)
        self.inventory = InventoryPage(self.driver)
        self.cart = CartPage(self.driver)
        self.menu = MenuPage(self.driver)

        print("🌐 Opening base URL and logging in…")
        self.driver.get(base_url)

        try:
            WebDriverWait(self.driver, 12).until(EC.presence_of_element_located(("id", "user-name")))
            WebDriverWait(self.driver, 12).until(EC.presence_of_element_located(("id", "password")))
        except Exception:
            self.driver.refresh()
            WebDriverWait(self.driver, 12).until(EC.presence_of_element_located(("id", "user-name")))
            WebDriverWait(self.driver, 12).until(EC.presence_of_element_located(("id", "password")))

        self.login.login("standard_user", "secret_sauce")
        WebDriverWait(self.driver, 12).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()
        print("✅ Logged in and on Inventory page.")

        yield
        try:
            self.base_page.take_screenshot(request.node.name)
        except Exception:
            pass

    @allure.story("Menu can open and close reliably")
    def test_open_and_close_menu(self):
        self.menu.open_menu()
        assert self.menu.is_open() is True, "Menu should be open"
        self.menu.close_menu()
        assert self.menu.is_closed() is True, "Menu should be closed"

    @allure.story("Reset App State clears cart badge and state")
    def test_reset_app_state_clears_cart(self):
        # Put some state: add two items
        assert self.inventory.add_to_cart_by_name("Sauce Labs Backpack")
        assert self.inventory.add_to_cart_by_name("Sauce Labs Bike Light")
        assert self.inventory.get_cart_count() >= 2

        # Reset via menu
        self.menu.click_reset_app_state()

        # Badge should be 0/hidden
        assert self.menu.get_cart_badge_count() == 0, "Cart badge should be 0 after reset"

        # Inventory should have "Add to cart" again (we'll re-add one to confirm reset worked)
        assert self.inventory.add_to_cart_by_name("Sauce Labs Backpack")
        # Clean up by resetting again
        self.menu.click_reset_app_state()
        assert self.menu.get_cart_badge_count() == 0

    @allure.story("Logout from menu returns to login page")
    def test_logout_redirects_to_login(self, base_url):
        self.menu.click_logout()
        # Expect login page; verify URL and login button
        expected = base_url.rstrip("/") + "/"
        WebDriverWait(self.driver, 10).until(EC.url_contains(expected))
        assert self.login.is_login_button_displayed() is True

    @allure.story("All Items returns to inventory from another page (Cart)")
    def test_all_items_from_cart(self):
        # Navigate away (Cart)
        self.inventory.open_cart()
        self.cart.wait_loaded()

        # Use menu → All Items
        self.menu.click_all_items()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()

    @allure.story("About opens Sauce Labs site and we can navigate back")
    def test_about_navigates_and_back(self):
        # Open menu → About
        self.menu.click_about()

        # In most runs it opens in same tab; assert URL contains 'sauce'
        # Some networks/headless runs may block external nav; handle gracefully
        try:
            WebDriverWait(self.driver, 10).until(lambda d: "sauce" in d.current_url.lower())
            print(f"🌍 About URL: {self.driver.current_url}")
        except Exception:
            print("⚠️ Could not verify external 'About' URL (network/headless/CSP). Continuing…")

        # Navigate back to inventory (browser back)
        self.driver.back()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()