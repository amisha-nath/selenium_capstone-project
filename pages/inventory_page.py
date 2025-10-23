# pages/inventory_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class InventoryPage:
    """
    Sauce Demo Inventory (Products) Page Object
    URL: https://www.saucedemo.com/inventory.html

    Uses string-based locator strategies to avoid `By` import.
    Includes a robust sort_by() with page-scroll, JS querySelector fallback,
    and JS-based set+change to defeat Edge clickability quirks.
    """

    def __init__(self, driver, timeout: int = 15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

        # ----- Locators -----
        self._inventory_container = ("id", "inventory_container")
        self._inventory_items = ("css selector", ".inventory_item")
        self._item_name = ".inventory_item_name"
        self._item_price = ".inventory_item_price"
        self._item_button = "button.btn_inventory"  # "Add to cart" or "Remove"
        # Keep both CSS and class-based fallbacks in comments for reference:
        #   select[data-test='product_sort_container']
        #   select.product_sort_container
        self._sort_select_css = "select[data-test='product_sort_container'], select.product_sort_container"
        self._cart_badge = ("css selector", ".shopping_cart_badge")
        self._cart_link = ("css selector", ".shopping_cart_link")

    # ===========================
    # Waits / Page State
    # ===========================
    def wait_loaded(self):
        """Block until the inventory container and at least one item are visible."""
        print("🕒 Waiting for Inventory page to load...")
        self.wait.until(EC.visibility_of_element_located(self._inventory_container))
        self.wait.until(EC.presence_of_all_elements_located(self._inventory_items))
        print("✅ Inventory page is visible and items are present.")

    # ===========================
    # Getters
    # ===========================
    def get_item_names(self):
        """Return the list of product names currently displayed."""
        self.wait_loaded()
        print("🔎 Collecting product names from inventory...")
        cards = self.driver.find_elements(*self._inventory_items)
        names = []
        for card in cards:
            try:
                names.append(card.find_element("css selector", self._item_name).text.strip())
            except Exception:
                pass
        print(f"📋 Found {len(names)} items: {names}")
        return names

    def get_item_prices(self):
        """Return the list of product prices (float)."""
        self.wait_loaded()
        print("🔎 Collecting product prices from inventory...")
        cards = self.driver.find_elements(*self._inventory_items)
        prices = []
        for card in cards:
            try:
                raw = card.find_element("css selector", self._item_price).text.strip()  # e.g., "$29.99"
                prices.append(float(raw.replace("$", "")))
            except Exception:
                pass
        print(f"💲 Prices: {prices}")
        return prices

    def get_cart_count(self) -> int:
        """Return the cart badge count; if badge is absent, return 0."""
        try:
            badge = self.driver.find_element(*self._cart_badge)
            count = int(badge.text.strip())
            print(f"🛒 Cart badge: {count}")
            return count
        except Exception:
            print("🛒 Cart badge not visible → treating as 0.")
            return 0

    # ===========================
    # Actions
    # ===========================
    def add_to_cart_by_name(self, name: str) -> bool:
        """
        Click 'Add to cart' for a given product name.
        Returns True if action performed, False if not found.
        """
        self.wait_loaded()
        print(f"➕ Adding '{name}' to cart...")
        cards = self.driver.find_elements(*self._inventory_items)
        for card in cards:
            try:
                title = card.find_element("css selector", self._item_name).text.strip()
                if title == name:
                    btn = card.find_element("css selector", self._item_button)
                    btn.click()
                    print(f"✅ Added '{name}' to cart.")
                    return True
            except Exception:
                continue
        print(f"❌ Item '{name}' not found on Inventory page.")
        return False

    def remove_from_cart_by_name(self, name: str) -> bool:
        """
        Click 'Remove' for a given product name.
        Returns True if removal performed, False if item not in cart or not found.
        """
        self.wait_loaded()
        print(f"➖ Removing '{name}' from cart...")
        cards = self.driver.find_elements(*self._inventory_items)
        for card in cards:
            try:
                title = card.find_element("css selector", self._item_name).text.strip()
                if title == name:
                    btn = card.find_element("css selector", self._item_button)
                    if "Remove" in btn.text:
                        btn.click()
                        print(f"✅ Removed '{name}' from cart.")
                        return True
                    else:
                        print(f"ℹ️ Button is not 'Remove' (text='{btn.text}') — item may not be in cart.")
                        return False
            except Exception:
                continue
        print(f"❌ Item '{name}' not found on Inventory page.")
        return False

    # ---------- internal: robust find for sort select ----------
    def _get_sort_select_element(self):
        """
        Robustly fetch the sort <select> using JS querySelector with fallback retries.
        This avoids EC presence flakiness observed on Edge in some runs.
        """
        # Try a short JS-based wait that polls for querySelector to return the element
        def _qs():
            return self.driver.execute_script(
                "return document.querySelector(arguments[0]);",
                self._sort_select_css
            )

        # Poll up to ~5s for the element via JS (fewer moving parts than EC)
        select_el = None
        end = WebDriverWait(self.driver, 5)
        try:
            select_el = end.until(lambda d: _qs())
        except Exception:
            # As a last fallback, do an EC presence on the likely CSS to produce a clean error if truly missing
            print("ℹ️ JS querySelector did not find sort select in 5s; trying EC presence fallback...")
            try:
                select_el = self.wait.until(
                    EC.presence_of_element_located(("css selector", "select[data-test='product_sort_container']"))
                )
            except Exception:
                # Final attempt using class-based selector
                select_el = self.wait.until(
                    EC.presence_of_element_located(("css selector", "select.product_sort_container"))
                )
        return select_el

    def sort_by(self, value: str):
        """
        Select a sort option by its value.
        Valid values (as per Sauce Demo): 'az', 'za', 'lohi', 'hilo'

        Robustness strategy:
          1) Page scroll: bottom -> top to stabilize layout/focus (helps Edge)
          2) Locate select via JS querySelector with retries
          3) Scroll the select into view
          4) Try Selenium Select; if it fails, fallback to JS (set value + dispatch 'change')
          5) Re-wait inventory container and (optionally) names change
        """
        print(f"↕️ Applying sort value: '{value}' ...")

        # Capture names before sort (to optionally detect change)
        before_names = self.get_item_names()

        # 1) Page scroll bottom → top (stabilizes clickability/layout)
        try:
            self.driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'instant'});")
            self.driver.execute_script("window.scrollTo({top: 0, behavior: 'instant'});")
        except Exception:
            pass

        # 2) Robustly get the select element
        select_el = self._get_sort_select_element()

        # 3) Scroll select into view (centered)
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_el)
        except Exception:
            pass
        # 4) Prefer Selenium Select; if fails, JS fallback
        try:
            try:
                self.wait.until(EC.element_to_be_clickable(("css selector", self._sort_select_css)))
            except Exception:
                print("ℹ️ Sort select not reported clickable; proceeding anyway.")

            from selenium.webdriver.support.ui import Select
            Select(select_el).select_by_value(value)
            print("✅ Sorting applied via Selenium Select.")
        except Exception as e:
            print(f"⚠️ Selenium Select failed ({e}); applying JS set + change event.")
            try:
                self.driver.execute_script(
                    """
                    const sel = arguments[0];
                    const val = arguments[1];
                    sel.value = val;
                    sel.dispatchEvent(new Event('change', {bubbles: true}));
                    """,
                    select_el, value
                )
                print("✅ Sorting applied via JS fallback.")
            except Exception as js_e:
                print(f"❌ JS fallback failed: {js_e}")
                raise

        # 5) Re-wait container and (optionally) list change
        try:
            self.wait.until(EC.visibility_of_element_located(self._inventory_container))
        except Exception:
            pass

        try:
            WebDriverWait(self.driver, 4).until(lambda d: self.get_item_names() != before_names)
        except Exception:
            # Small datasets may not visibly reorder for some sorts; tolerate
            pass
        print("✅ Sorting applied (finalized).")

    def open_product_by_name(self, name: str) -> bool:
        """
        Click on the product name link to open the Product Details page.
        Returns True if navigation triggered, False if not found.
        """
        self.wait_loaded()
        print(f"🔗 Opening product details for '{name}' ...")
        cards = self.driver.find_elements(*self._inventory_items)
        for card in cards:
            try:
                link = card.find_element("css selector", self._item_name)
                if link.text.strip() == name:
                    link.click()
                    print(f"✅ Navigated to details for '{name}'.")
                    return True
            except Exception:
                continue
        print(f"❌ Could not find '{name}' to open details.")
        return False

    def open_cart(self):
        """Open the Cart page by clicking the cart icon in the header."""
        print("🧭 Navigating to Cart page...")
        self.wait.until(EC.element_to_be_clickable(self._cart_link)).click()
        print("✅ Cart page opened.")