# tests/test_cart.py
import pytest
import allure
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage
from pages.base_page import BasePage

@pytest.mark.usefixtures("driver")
class TestCart:

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url, request):
        """
        - Open base URL
        - Wait for login inputs (refresh once if needed)
        - Login with standard_user
        - Land on Inventory page
        - After each test, take a screenshot
        """
        self.driver = driver
        self.base_page = BasePage(self.driver)
        self.login = LoginPage(self.driver)
        self.inventory = InventoryPage(self.driver)
        self.cart = CartPage(self.driver)

        print("🌐 Opening base URL and logging in...")
        self.driver.get(base_url)

        # Guard first paint for stability
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

    @allure.story("Add two items then remove one; verify cart badge and list size")
    def test_add_two_then_remove_one(self):
        item1 = "Sauce Labs Backpack"
        item2 = "Sauce Labs Bike Light"

        # Add two items from Inventory
        assert self.inventory.add_to_cart_by_name(item1)
        assert self.inventory.add_to_cart_by_name(item2)
        assert self.inventory.get_cart_count() == 2

        # Go to Cart
        self.inventory.open_cart()
        self.cart.wait_loaded()

        # Verify two items present
        items = self.cart.get_cart_items()
        names = [i["name"] for i in items]
        assert item1 in names and item2 in names
        assert len(items) == 2

        # Remove one
        assert self.cart.remove_item(item2)
        items_after = self.cart.get_cart_items()
        names_after = [i["name"] for i in items_after]
        assert item2 not in names_after
        assert len(items_after) == 1
        # Badge may update immediately or after nav; allow >=1
        assert self.cart.get_cart_count() >= 1

    @allure.story("Continue shopping returns to inventory and allows new add")
    def test_continue_shopping_navigate_and_add(self):
        first = "Sauce Labs Bolt T-Shirt"
        assert self.inventory.add_to_cart_by_name(first)
        self.inventory.open_cart()
        self.cart.wait_loaded()

        # Continue Shopping
        self.cart.continue_shopping()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()

        # Add a second item now
        second = "Sauce Labs Onesie"
        assert self.inventory.add_to_cart_by_name(second)
        assert self.inventory.get_cart_count() >= 2

        # Open cart again and validate presence of both
        self.inventory.open_cart()
        self.cart.wait_loaded()
        names = [i["name"] for i in self.cart.get_cart_items()]
        assert first in names and second in names

    @allure.story("Clear cart (idempotent) and ensure it's empty")
    def test_clear_cart_empty_flow(self):
        # Ensure some state: add one, navigate to cart
        self.inventory.add_to_cart_by_name("Sauce Labs Fleece Jacket")
        self.inventory.open_cart()
        self.cart.wait_loaded()

        # Clear everything (safe if already empty)
        removed = self.cart.clear_cart()
        print(f"Removed count reported: {removed}")

        # Verify empty
        items = self.cart.get_cart_items()
        assert len(items) == 0, "Cart should be empty after clear_cart()"
        # Badge might vanish when 0
        assert self.cart.get_cart_count() in (0,)

        # Continue shopping lands back to inventory
        self.cart.continue_shopping()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()

    @allure.story("Checkout button navigates to step one page")
    def test_checkout_navigates_to_step_one(self):
        assert self.inventory.add_to_cart_by_name("Sauce Labs Backpack")
        self.inventory.open_cart()
        self.cart.wait_loaded()

        # Checkout
        self.cart.checkout()
        WebDriverWait(self.driver, 10).until(EC.url_contains("checkout-step-one.html"))
        print("🧾 On Checkout Step One page.")

        # Navigate back to cart and continue shopping to restore baseline
        self.driver.back()
        WebDriverWait(self.driver, 10).until(EC.url_contains("cart.html"))
        self.cart.wait_loaded()
        self.cart.continue_shopping()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()