# tests/test_product_details.py
import pytest
import allure
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.product_details_page import ProductDetailsPage
from pages.base_page import BasePage

@pytest.mark.usefixtures("driver")
class TestProductDetails:

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
        self.details = ProductDetailsPage(self.driver)

        print("🌐 Opening base URL and logging in...")
        self.driver.get(base_url)
        self.login.login("standard_user", "secret_sauce")
        WebDriverWait(self.driver, 12).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()
        print("✅ Logged in and on Inventory page.")
        yield
        try:
            self.base_page.take_screenshot(request.node.name)
        except Exception:
            pass

    @allure.story("Details URL and image validation (XPath)")
    def test_details_url_and_image_meta(self):
        product = "Sauce Labs Backpack"

        # Open details from inventory (uses Inventory POM)
        assert self.inventory.open_product_by_name(product), f"Could not open details for '{product}'"

        # URL should contain details page and have id param
        item_id = self.details.current_item_id()
        assert "inventory-item.html" in self.driver.current_url, "URL should be details page"
        assert item_id is not None, "Details URL should include an item id"

        # Image should have a src and be fully loaded
        assert self.details.image_src() != "", "Image src should not be empty"
        assert self.details.is_image_loaded() is True, "Product image should be loaded"

        # Basic content signals via POM (XPath inside)
        assert self.details.get_title() == product, "Title mismatch on details page"
        assert self.details.get_description() != "", "Description should not be empty"
        assert self.details.get_price() > 0.0, "Price should be positive"

    @allure.story("Add on details and verify state persists across back/forward (XPath)")
    def test_add_persists_across_navigation(self):
        product = "Sauce Labs Bike Light"

        # Open details and add to cart
        assert self.inventory.open_product_by_name(product)
        start_badge = self.details.get_cart_count()
        added = self.details.add_to_cart()
        if added:
            assert self.details.is_in_cart() is True, "Should be in cart after add"
            assert self.details.get_cart_count() == start_badge + 1, "Cart badge should increment"

        # Browser back to inventory
        print("⬅️  Browser back to inventory...")
        self.driver.back()
        WebDriverWait(self.driver, 12).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()

        # Browser forward back to details
        print("➡️  Browser forward back to details...")
        self.driver.forward()
        self.details.wait_loaded()

        # State should persist
        assert self.details.is_in_cart() is True, "State should persist after back/forward"
        assert self.details.get_cart_count() >= start_badge + 1, "Badge should reflect previously added item"

        # Cleanup: remove from cart and verify badge not increased
        self.details.remove_from_cart()
        assert self.details.is_in_cart() is False, "Should not be in cart after removal"
        assert self.details.get_cart_count() >= start_badge, "Badge should not increase after removal"

        # Back to products
        self.details.back_to_products()
        WebDriverWait(self.driver, 12).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()

    @allure.story("Open Cart from details header then continue shopping (XPath)")
    def test_open_cart_from_details_header(self):
        product = "Sauce Labs Fleece Jacket"

        # Open details and add to cart (idempotent)
        assert self.inventory.open_product_by_name(product)
        start_badge = self.details.get_cart_count()
        self.details.add_to_cart()
        assert self.details.get_cart_count() >= start_badge + 1, "Badge should increment after add"

        # Open Cart via header link from details (XPath inside POM)
        self.details.open_cart_from_header()
        WebDriverWait(self.driver, 12).until(EC.url_contains("cart.html"))
        print("🧾 On Cart page via header from details.")

        # ✅ Use "Continue Shopping" on Cart to return to Inventory (XPath)
        continue_btn = WebDriverWait(self.driver, 12).until(
            EC.element_to_be_clickable(("xpath", "//button[@id='continue-shopping']"))
        )
        continue_btn.click()
        WebDriverWait(self.driver, 12).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()

    @allure.story("Window controls (maximize/minimize/resize) + navigation (back/forward) with XPath interactions")
    def test_window_controls_and_browser_navigation(self):
        """
        - Open details via POM (XPath)
        - Maximize → Minimize (fallback) → Restore (maximize) → Resize
        - Open Cart from header (XPath)
        - Back → Details, Back → Inventory, Forward → Details
        """
        product = "Sauce Labs Onesie"

        # Open details
        assert self.inventory.open_product_by_name(product), f"Could not open details for '{product}'"
        self.details.wait_loaded()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory-item.html"))
        print("🔗 On Product Details page.")

        # Window controls
        try:
            print("🧰 Maximizing window...")
            self.driver.maximize_window()
        except Exception as e:
            print(f"⚠️ maximize_window() failed: {e}")

        try:
            print("🧰 Minimizing window...")
            self.driver.minimize_window()  # Selenium 4+
        except Exception as e:
            print(f"⚠️ minimize_window() failed: {e}. Using small size fallback.")
            try:
                self.driver.set_window_rect(x=0, y=0, width=300, height=200)
            except Exception as ie:
                print(f"❌ set_window_rect fallback failed: {ie}")

        # Restore and set custom size
        try:
            print("🧰 Restoring via maximize...")
            self.driver.maximize_window()
        except Exception:
            pass
        try:
            print("🧰 Setting custom window size 1280x800...")
            self.driver.set_window_size(1280, 800)
        except Exception as e:
            print(f"⚠️ set_window_size failed: {e}")

        # Open Cart from header (XPath in POM)
        self.details.open_cart_from_header()
        WebDriverWait(self.driver, 10).until(EC.url_contains("cart.html"))
        print("🧾 On Cart page.")

        # Back → should go to Details
        print("⬅️  Browser back...")
        self.driver.back()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory-item.html"))
        self.details.wait_loaded()
        print("🔙 Back to Details (via history).")

        # Back → should go to Inventory
        print("⬅️  Browser back...")
        self.driver.back()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()
        print("🔙 Back to Inventory (via history).")

        # Forward → should go back to Details
        print("➡️  Browser forward...")
        self.driver.forward()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory-item.html"))
        self.details.wait_loaded()
        print("➡️ Forward to Details (via history).")