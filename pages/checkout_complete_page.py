# pages/checkout_complete_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CheckoutCompletePage:
    """
    Sauce Demo Checkout Complete (Thank You) — XPath-only POM
    URL: https://www.saucedemo.com/checkout-complete.html
    """

    def __init__(self, driver, timeout: int = 12):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

        # ----- XPath Locators -----
        self._container_x   = ("xpath", "//div[contains(@class,'checkout_complete_container')]")
        self._header_x      = ("xpath", "//h2[contains(@class,'complete-header')]")
        self._text_x        = ("xpath", "//div[contains(@class,'complete-text')]")
        self._back_home_x   = ("xpath", "//button[@id='back-to-products']")
        self._image_x       = ("xpath", "//img[contains(@class,'pony_express')]")  # optional

    # ===========================
    # Wait / State
    # ===========================
    def wait_loaded(self):
        print("🕒 Waiting for Checkout Complete page to load...")
        self.wait.until(EC.visibility_of_element_located(self._container_x))
        self.wait.until(EC.visibility_of_element_located(self._header_x))
        print("✅ Checkout Complete page is visible.")

    # ===========================
    # Getters
    # ===========================
    def get_header_text(self) -> str:
        self.wait_loaded()
        txt = self.driver.find_element(*self._header_x).text.strip()
        print(f"🏁 Complete header: {txt}")
        return txt

    def get_body_text(self) -> str:
        self.wait_loaded()
        txt = self.driver.find_element(*self._text_x).text.strip()
        print(f"📝 Complete body: {txt}")
        return txt

    def is_thank_you_visible(self) -> bool:
        try:
            self.wait_loaded()
            header = self.driver.find_element(*self._header_x).text.strip().lower()
            visible = "thank you" in header
            print(f"👀 Thank-you visible? {visible}")
            return visible
        except Exception:
            print("👀 Thank-you header not visible.")
            return False

    # ===========================
    # Actions
    # ===========================
    def back_home(self):
        """Click 'Back Home' to return to the Inventory page."""
        print("🏠 Clicking 'Back Home'...")
        btn = self.wait.until(EC.element_to_be_clickable(self._back_home_x))
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        except Exception:
            pass
        try:
            btn.click()
        except Exception as e:
            print(f"⚠️ Normal click failed: {e}; trying JS click...")
            self.driver.execute_script("arguments[0].click();", btn)
        print("✅ Back Home clicked.")