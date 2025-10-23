# tests/test_checkout_complete_e2e.py
import math
import pytest
import allure
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage
from pages.checkout_complete_page import CheckoutCompletePage

def _float_eq(a: float, b: float, tol: float = 1e-2) -> bool:
    return math.isclose(a, b, rel_tol=0, abs_tol=tol)

@pytest.mark.usefixtures("driver")
class TestCheckoutCompleteE2E:

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url, request):
        """
        - Open base URL
        - Guard login inputs (refresh once if needed)
        - Login and land on Inventory
        - After each test, take a screenshot
        """
        self.driver = driver
        self.base_page = BasePage(self.driver)
        self.login = LoginPage(self.driver)
        self.inventory = InventoryPage(self.driver)
        self.cart = CartPage(self.driver)
        self.complete = CheckoutCompletePage(self.driver)

        print("🌐 Opening base URL and logging in...")
        self.driver.get(base_url)

        # Guard first paint of login inputs (stability)
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

    @allure.story("Add two items, verify price + tax + total, finish checkout, and go back home")
    def test_complete_checkout_two_items_verify_totals_and_back(self):
        # 1) Add two items
        items = ["Sauce Labs Backpack", "Sauce Labs Bike Light"]
        for name in items:
            print(f"👜 Adding item: {name}")
            assert self.inventory.add_to_cart_by_name(name), f"Failed adding '{name}'"
        print(f"🛒 Cart badge after add: {self.inventory.get_cart_count()}")

        # 2) Go to Cart
        self.inventory.open_cart()
        self.cart.wait_loaded()

        # 3) Checkout (Step One) — XPath inline (no POM for step 1/2)
        print("🧭 Proceeding to Checkout Step One...")
        checkout_btn_x = ("xpath", "//button[@id='checkout']")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(checkout_btn_x)).click()
        WebDriverWait(self.driver, 10).until(EC.url_contains("checkout-step-one.html"))

        # Fill Step One
        print("📝 Filling Step One (Your Information)...")
        first_x = ("xpath", "//input[@id='first-name']")
        last_x  = ("xpath", "//input[@id='last-name']")
        postal_x= ("xpath", "//input[@id='postal-code']")
        cont_x  = ("xpath", "//input[@id='continue' or @data-test='continue']")

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(first_x)).send_keys("Amisha")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(last_x)).send_keys("Nath")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(postal_x)).send_keys("560001")
        # click continue with scroll/JS safety
        cont_btn = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(cont_x))
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cont_btn)
        except Exception:
            pass
        try:
            cont_btn.click()
        except Exception as e:
            print(f"⚠️ Continue normal click failed: {e}; trying JS click...")
            self.driver.execute_script("arguments[0].click();", cont_btn)

        # 4) Step Two — Verify prices + tax + total
        WebDriverWait(self.driver, 10).until(EC.url_contains("checkout-step-two.html"))
        print("🧮 Verifying line prices, item total, tax, and grand total...")

        # Collect line prices
        price_cells_x = ("xpath", "//div[contains(@class,'inventory_item_price')]")
        price_elems = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located(price_cells_x))
        line_prices = []
        for el in price_elems:
            try:
                line_prices.append(float(el.text.strip().replace("$", "")))
            except Exception:
                pass
        print(f"💵 Line item prices: {line_prices}")
        computed_item_total = round(sum(line_prices), 2)

        # Read summary labels
        item_total_x = ("xpath", "//div[contains(@class,'summary_subtotal_label')]")
        tax_x        = ("xpath", "//div[contains(@class,'summary_tax_label')]")
        total_x      = ("xpath", "//div[contains(@class,'summary_total_label')]")

        def _parse_amount(text: str) -> float:
            try:
                return float(text.split("$")[-1].strip())
            except Exception:
                return 0.0

        item_total_val = _parse_amount(WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(item_total_x)).text.strip())
        tax_val = _parse_amount(WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(tax_x)).text.strip())
        total_val = _parse_amount(WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(total_x)).text.strip())

        print(f"🧾 Summary -> Item total: {item_total_val}, Tax: {tax_val}, Total: {total_val}")
        print(f"🧮 Computed item total from lines: {computed_item_total}")

        assert _float_eq(item_total_val, computed_item_total), \
            f"Item total mismatch. Summary={item_total_val}, Computed={computed_item_total}"
        assert _float_eq(total_val, round(item_total_val + tax_val, 2)), \
            f"Grand total mismatch. Summary={total_val}, Computed={round(item_total_val + tax_val, 2)}"

        # 5) Finish checkout
        print("✅ Clicking Finish...")
        finish_btn_x = ("xpath", "//button[@id='finish']")
        try:
            btn = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(finish_btn_x))
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            except Exception:
                pass
            btn.click()
        except Exception as e:
            print(f"⚠️ Finish normal click failed: {e}; trying JS click...")
            btn = self.driver.find_element(*finish_btn_x)
            self.driver.execute_script("arguments[0].click();", btn)

        # 6) Validate Checkout Complete and go back home
        WebDriverWait(self.driver, 10).until(EC.url_contains("checkout-complete.html"))
        self.complete.wait_loaded()
        assert self.complete.is_thank_you_visible() is True, "Thank-you header should be visible"
        print("🎉 Checkout complete page validated.")

        self.complete.back_home()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        self.inventory.wait_loaded()
        print("🏠 Back on Inventory page.")