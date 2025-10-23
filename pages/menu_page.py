# pages/menu_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class MenuPage:
    """
    Sauce Demo Burger Menu (left side) — XPath-only POM
    Provides safe open/close and actions: All Items, About, Logout, Reset App State.
    """

    def __init__(self, driver, timeout: int = 15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

        # --- Header / Buttons ---
        self._burger_btn_x   = ("xpath", "//button[@id='react-burger-menu-btn']")
        self._close_btn_x    = ("xpath", "//button[@id='react-burger-cross-btn']")
        self._cart_link_x    = ("xpath", "//a[contains(@class,'shopping_cart_link')]")
        self._cart_badge_x   = ("xpath", "//span[contains(@class,'shopping_cart_badge')]")

        # --- Menu panel / items ---
        self._menu_panel_x   = ("xpath", "//nav[contains(@class,'bm-item-list') or contains(@class,'bm-menu')]")
        self._all_items_x    = ("xpath", "//a[@id='inventory_sidebar_link']")
        self._about_x        = ("xpath", "//a[@id='about_sidebar_link']")
        self._logout_x       = ("xpath", "//a[@id='logout_sidebar_link']")
        self._reset_x        = ("xpath", "//a[@id='reset_sidebar_link']")

    # -------------------------
    # Helpers
    # -------------------------
    def _safe_click(self, locator):
        """Click with scroll + JS fallback (for click interception)."""
        el = self.wait.until(EC.presence_of_element_located(locator))
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        except Exception:
            pass
        try:
            self.wait.until(EC.element_to_be_clickable(locator)).click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", el)

    def _is_present_and_displayed(self, locator) -> bool:
        try:
            el = self.driver.find_element(*locator)
            return el.is_displayed()
        except Exception:
            return False

    # -------------------------
    # State
    # -------------------------
    def is_open(self) -> bool:
        """Menu is open when close button or panel is visible."""
        return self._is_present_and_displayed(self._close_btn_x) or self._is_present_and_displayed(self._menu_panel_x)

    def is_closed(self) -> bool:
        return not self.is_open()

    def get_cart_badge_count(self) -> int:
        """Return cart badge (0 if hidden)."""
        try:
            el = self.driver.find_element(*self._cart_badge_x)
            return int(el.text.strip())
        except Exception:
            return 0

    # -------------------------
    # Actions
    # -------------------------
    def open_menu(self):
        print("🍔 Opening menu…")
        self._safe_click(self._burger_btn_x)
        # wait for a menu item to be visible
        self.wait.until(EC.visibility_of_element_located(self._all_items_x))
        print("✅ Menu opened.")

    def close_menu(self):
        print("❎ Closing menu…")
        self._safe_click(self._close_btn_x)
        # wait until the menu is closed
        self.wait.until(lambda d: self.is_closed())
        print("✅ Menu closed.")

    def click_all_items(self):
        print("📦 Clicking 'All Items'…")
        if not self.is_open():
            self.open_menu()
        self._safe_click(self._all_items_x)
        print("➡️ Navigating to Inventory via All Items…")

    def click_about(self):
        print("ℹ️ Clicking 'About'…")
        if not self.is_open():
            self.open_menu()
        self._safe_click(self._about_x)
        print("➡️ Navigating to external About (Sauce Labs)…")

    def click_logout(self):
        print("🚪 Clicking 'Logout'…")
        if not self.is_open():
            self.open_menu()
        self._safe_click(self._logout_x)
        print("➡️ Logged out / Navigating to login page…")

    def click_reset_app_state(self):
        print("🧹 Clicking 'Reset App State'…")
        if not self.is_open():
            self.open_menu()
        self._safe_click(self._reset_x)
        # After reset, close the menu to reflect header badge changes
        try:
            self.close_menu()
        except Exception:
            pass
        print("✅ App state reset.")

    def open_cart(self):
        print("🛒 Opening Cart from header…")
        self._safe_click(self._cart_link_x)
        print("➡️ Cart opened.")