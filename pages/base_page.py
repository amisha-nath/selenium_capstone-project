# pages/base_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os

try:
    import allure
except Exception:
    allure = None

from utils.logger import get_logger
logger = get_logger()

class BasePage:
    """Base class for all page objects — contains common Selenium actions with explicit waits."""

    def __init__(self, driver, timeout: int = 10):
        self.driver = driver
        self.timeout = timeout

    def open_url(self, url: str):
        logger.info(f"Opening URL: {url}")
        self.driver.get(url)

    def find_element(self, locator):
        try:
            element = WebDriverWait(self.driver, self.timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return element
        except TimeoutException:
            logger.error(f"Element not found or not visible: {locator}")
            self.take_screenshot("element_not_found")
            raise

    def click(self, locator):
        logger.info(f"🖱 Clicking element: {locator}")
        element = self.find_element(locator)
        element.click()

    def send_keys(self, locator, text: str):
        logger.info(f"⌨ Typing into {locator}: '{text}'")
        element = self.find_element(locator)
        element.clear()
        element.send_keys(text)

    def get_text(self, locator) -> str:       # ← fixed
        element = self.find_element(locator)
        return element.text

    def is_visible(self, locator) -> bool:    # ← fixed
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.visibility_of_element_located(locator)
            )
            logger.info(f"Element visible: {locator}")
            return True
        except TimeoutException:
            logger.warning(f" Element not visible: {locator}")
            return False

    def take_screenshot(self, name: str):
        """Capture a screenshot and attach to Allure if available."""
        os.makedirs("screenshots", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = f"screenshots/{name}_{timestamp}.png"
        try:
            self.driver.save_screenshot(path)
            logger.info(f" Screenshot saved: {path}")
            if allure:
                try:
                    allure.attach.file(path, name=name, attachment_type=allure.attachment_type.PNG)
                except Exception:
                    logger.debug("Could not attach screenshot to Allure.")
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")