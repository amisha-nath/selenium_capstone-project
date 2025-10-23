# tests/test_inventory.py
import pytest
import allure
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.base_page import BasePage

@pytest.mark.usefixtures("driver")
class TestInventory:

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url, request):
        """
        - Open base URL
        - Login with standard_user
        - Land on Inventory page
        - After each test, take a screenshot (attached to Allure if available)
        """
        self.driver = driver
        self.base_page = BasePage(self.driver)
        self.login = LoginPage(self.driver)
        self.inventory = InventoryPage(self.driver)

        print("🌐 Opening base URL and logging in...")
        self.driver.get(base_url)
        self.login.login("standard_user", "secret_sauce")
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()
        print("✅ Logged in and on Inventory page.")

        yield
        # Always capture a screenshot at the end of the test
        try:
            self.base_page.take_screenshot(request.node.name)
        except Exception:
            # Don't block teardown on screenshot issues
            pass

    @allure.story("Add & Remove a product; verify cart badge updates")
    def test_add_remove_updates_cart_badge(self):
        product = "Sauce Labs Backpack"

        # Add item
        assert self.inventory.add_to_cart_by_name(product) is True, "Failed to add item to cart"
        assert self.inventory.get_cart_count() == 1, "Cart badge should be 1 after add"

        # Remove item
        assert self.inventory.remove_from_cart_by_name(product) is True, "Failed to remove item from cart"
        assert self.inventory.get_cart_count() == 0, "Cart badge should return to 0 after remove"

    @allure.story("Sorting by Name and Price")
    def test_sorting_name_and_price(self):
        # 🔧 Extra nudge: global scroll bottom → top (helps Edge stabilize),
        # even though InventoryPage.sort_by() also performs scrolls.
        try:
            self.driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'instant'});")
            self.driver.execute_script("window.scrollTo({top: 0, behavior: 'instant'});")
        except Exception:
            pass

        # Name A→Z
        self.inventory.sort_by("az")
        names_az = self.inventory.get_item_names()
        assert names_az == sorted(names_az), "Names should be sorted ascending (A→Z)"

        # Name Z→A
        self.inventory.sort_by("za")
        names_za = self.inventory.get_item_names()
        assert names_za == sorted(names_za, reverse=True), "Names should be sorted descending (Z→A)"

        # Price low→high
        self.inventory.sort_by("lohi")
        prices_lohi = self.inventory.get_item_prices()
        assert prices_lohi == sorted(prices_lohi), "Prices should be ascending (low→high)"

        # Price high→low
        self.inventory.sort_by("hilo")
        prices_hilo = self.inventory.get_item_prices()
        assert prices_hilo == sorted(prices_hilo, reverse=True), "Prices should be descending (high→low)"

    @allure.story("Open product details and navigate back to products")
    def test_open_product_details_and_back(self):
        product = "Sauce Labs Backpack"

        # Open details
        assert self.inventory.open_product_by_name(product) is True, f"Could not open details for '{product}'"

        # Validate details page title matches
        title_el = WebDriverWait(self.driver, 10).until(
            lambda d: d.find_element("css selector", ".inventory_details_name")
        )
        assert title_el.text.strip() == product, "Product title mismatch on details page"

        # Back to inventory
        print("🔙 Navigating back to products...")
        back_btn = WebDriverWait(self.driver, 10).until(lambda d: d.find_element("id", "back-to-products"))
        back_btn.click()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()
        print("✅ Back on Inventory page.")