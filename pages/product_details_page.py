# pages/product_details_page.py
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ProductDetailsPage:
    """
    Sauce Demo Product Details Page Object
    Example URL: https://www.saucedemo.com/inventory-item.html?id=4

    ✨ All element locators in this POM are XPath-based.
    """

    def __init__(self, driver, timeout: int = 12):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

        # ----- XPath Locators -----
        self._title_x = ("xpath", "//div[contains(@class,'inventory_details_name')]")
        self._desc_x = ("xpath", "//div[contains(@class,'inventory_details_desc')]")
        self._price_x = ("xpath", "//div[contains(@class,'inventory_details_price')]")
        self._primary_btn_x = ("xpath", "//button[contains(@class,'btn_inventory')]")  # "Add to cart" / "Remove"
        self._back_btn_x = ("xpath", "//button[@id='back-to-products']")
        self._cart_badge_x = ("xpath", "//span[contains(@class,'shopping_cart_badge')]")
        self._cart_link_x = ("xpath", "//a[contains(@class,'shopping_cart_link')]")
        self._image_x = ("xpath", "//img[contains(@class,'inventory_details_img')]")

    # ===========================
    # Waits / Page State
    # ===========================
    def wait_loaded(self):
        """Wait until the details title is visible."""
        print("🕒 Waiting for Product Details page to load...")
        self.wait.until(EC.visibility_of_element_located(self._title_x))
        print("✅ Details page is visible.")

    # ===========================
    # URL helpers
    # ===========================
    def current_item_id(self) -> str | None:
        """
        Parse the current URL and return the `id` query parameter, e.g., "4".
        Returns None if not present.
        """
        self.wait_loaded()
        url = self.driver.current_url
        parsed = urlparse(url)
        q = parse_qs(parsed.query)
        item_id = q.get("id", [None])[0]
        print(f"🔗 URL: {url} | item_id={item_id}")
        return item_id

    # ===========================
    # Content getters
    # ===========================
    def get_title(self) -> str:
        self.wait_loaded()
        text = self.driver.find_element(*self._title_x).text.strip()
        print(f"🏷  Title: {text}")
        return text

    def get_description(self) -> str:
        self.wait_loaded()
        text = self.driver.find_element(*self._desc_x).text.strip()
        print(f"📝 Description: {text[:80]}{'...' if len(text) > 80 else ''}")
        return text

    def get_price(self) -> float:
        self.wait_loaded()
        raw = self.driver.find_element(*self._price_x).text.strip()  # e.g., "$29.99"
        price = float(raw.replace("$", ""))
        print(f"💲 Price: {price}")
        return price

    def image_src(self) -> str:
        """Return the image src URL."""
        self.wait_loaded()
        src = self.driver.find_element(*self._image_x).get_attribute("src") or ""
        print(f"🖼  Image src: {src}")
        return src

    def is_image_loaded(self) -> bool:
        """
        Verify that the product image is actually loaded in the browser.
        """
        self.wait_loaded()
        img = self.driver.find_element(*self._image_x)
        loaded = bool(self.driver.execute_script(
            "return arguments[0].complete && arguments[0].naturalWidth > 0;", img
        ))
        print(f"🖼  Image loaded? {loaded}")
        return loaded

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

    def is_in_cart(self) -> bool:
        """
        Determine if current product is in cart by checking primary button text ("Remove").
        """
        self.wait_loaded()
        try:
            btn_text = self.driver.find_element(*self._primary_btn_x).text.strip().lower()
            in_cart = "remove" in btn_text
            print(f"🧩 is_in_cart? {in_cart} (button='{btn_text}')")
            return in_cart
        except Exception:
            return False

    # ===========================
    # Actions
    # ===========================
    def add_to_cart(self) -> bool:
        """
        Click 'Add to cart' if available.
        Returns True if click performed, False if already in cart.
        """
        self.wait_loaded()
        btn = self.driver.find_element(*self._primary_btn_x)
        label = btn.text.strip().lower()
        if "add to cart" in label:
            print("➕ Clicking 'Add to cart'...")
            btn.click()
            return True
        print(f"ℹ️ Not adding. Button label is '{label}' (already in cart?).")
        return False

    def remove_from_cart(self) -> bool:
        """
        Click 'Remove' if available.
        Returns True if click performed, False if not in cart.
        """
        self.wait_loaded()
        btn = self.driver.find_element(*self._primary_btn_x)
        label = btn.text.strip().lower()
        if "remove" in label:
            print("➖ Clicking 'Remove'...")
            btn.click()
            return True
        print(f"ℹ️ Not removing. Button label is '{label}' (not in cart?).")
        return False

    def toggle_add_remove(self) -> str:
        """
        Toggle the primary button once and return the new label ('Remove' or 'Add to cart').
        """
        self.wait_loaded()
        btn = self.driver.find_element(*self._primary_btn_x)
        before = btn.text.strip()
        btn.click()
        # Wait for label to change
        self.wait.until(lambda d: d.find_element(*self._primary_btn_x).text.strip() != before)
        after = self.driver.find_element(*self._primary_btn_x).text.strip()
        print(f"🔁 Toggled button: '{before}' -> '{after}'")
        return after

    def back_to_products(self):
        """Click 'Back to products' and return to inventory page."""
        print("🔙 Clicking 'Back to products'...")
        self.wait.until(EC.element_to_be_clickable(self._back_btn_x)).click()
        print("✅ Back to products clicked.")

    def open_cart_from_header(self):
        """Open the cart page by clicking the cart icon in the header."""
        print("🧭 Opening Cart from header...")
        self.wait.until(EC.element_to_be_clickable(self._cart_link_x)).click()
        print("✅ Cart page opened from header.")
