# pages/cart_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CartPage:
    """
    Sauce Demo Cart Page Object (XPath-only locators)
    URL: https://www.saucedemo.com/cart.html
    """

    def __init__(self, driver, timeout: int = 12):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

        # ----- XPath Locators -----
        self._cart_list_x      = ("xpath", "//div[contains(@class,'cart_list')]")
        self._cart_item_x      = ("xpath", "//div[contains(@class,'cart_item')]")
        self._item_name_x_rel  = ".//div[contains(@class,'inventory_item_name')]"
        self._item_price_x_rel = ".//div[contains(@class,'inventory_item_price')]"
        self._item_qty_x_rel   = ".//div[contains(@class,'cart_quantity')]"
        self._remove_btn_x_rel = ".//button[contains(@class,'cart_button') or contains(.,'Remove')]"

        self._continue_btn_x   = ("xpath", "//button[@id='continue-shopping']")
        self._checkout_btn_x   = ("xpath", "//button[@id='checkout']")
        self._cart_badge_x     = ("xpath", "//span[contains(@class,'shopping_cart_badge')]")

    # ===========================
    # Waits / Page State
    # ===========================
    def wait_loaded(self):
        """Wait until the cart list is visible."""
        print("🕒 Waiting for Cart page to load...")
        self.wait.until(EC.visibility_of_element_located(self._cart_list_x))
        print("✅ Cart page is visible.")

    # ===========================
    # Getters
    # ===========================
    def get_cart_items(self):
        """
        Return a list of dicts representing items in cart:
        [{ "name": str, "price": float, "qty": int }, ...]
        """
        self.wait_loaded()
        print("🔎 Collecting items from cart...")
        rows = self.driver.find_elements(*self._cart_item_x)
        items = []
        for r in rows:
            try:
                name = r.find_element("xpath", self._item_name_x_rel).text.strip()
                price_raw = r.find_element("xpath", self._item_price_x_rel).text.strip().replace("$", "")
                qty_raw = r.find_element("xpath", self._item_qty_x_rel).text.strip()
                items.append({
                    "name": name,
                    "price": float(price_raw),
                    "qty": int(qty_raw) if qty_raw.isdigit() else 1
                })
            except Exception:
                pass
        print(f"📋 Cart items ({len(items)}): {items}")
        return items

    def get_cart_count(self) -> int:
        """Return the cart badge count; if badge is absent, return 0."""
        try:
            badge = self.driver.find_element(*self._cart_badge_x)
            count = int(badge.text.strip())
            print(f"🛒 Cart badge: {count}")
            return count
        except Exception:
            print("🛒 Cart badge not visible → treating as 0.")
            return 0

    def has_item(self, name: str) -> bool:
        """Return True if an item with the given name is present in the cart."""
        return any(i["name"] == name for i in self.get_cart_items())

    # ===========================
    # Actions
    # ===========================
    def remove_item(self, name: str) -> bool:
        """
        Click 'Remove' for a specific item by name.
        Returns True if removed, False if not found.
        """
        self.wait_loaded()
        print(f"➖ Removing '{name}' from cart...")
        rows = self.driver.find_elements(*self._cart_item_x)
        for r in rows:
            try:
                title = r.find_element("xpath", self._item_name_x_rel).text.strip()
                if title == name:
                    r.find_element("xpath", self._remove_btn_x_rel).click()
                    print(f"✅ Removed '{name}' from cart.")
                    return True
            except Exception:
                continue
        print(f"❌ Could not find '{name}' to remove.")
        return False

    def clear_cart(self) -> int:
        """
        Attempt to remove all items currently in the cart.
        Returns number of items removed.
        """
        self.wait_loaded()
        print("🧹 Clearing cart...")
        removed = 0
        while True:
            rows = self.driver.find_elements(*self._cart_item_x)
            if not rows:
                break
            try:
                rows[0].find_element("xpath", self._remove_btn_x_rel).click()
                removed += 1
            except Exception:
                break
        print(f"✅ Cleared {removed} item(s) from cart.")
        return removed

    def continue_shopping(self):
        """Click 'Continue Shopping' to return to the Inventory page."""
        print("🔙 Clicking 'Continue Shopping'...")
        self.wait.until(EC.element_to_be_clickable(self._continue_btn_x)).click()
        print("✅ Navigated back to Inventory.")

    def checkout(self):
        """Click 'Checkout' to navigate to Checkout Step One page."""
        print("🧭 Clicking 'Checkout'...")
        self.wait.until(EC.element_to_be_clickable(self._checkout_btn_x)).click()
        print("✅ Navigated to Checkout Step One page.")