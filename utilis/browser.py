from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from utils.logger import get_logger

logger = get_logger(__name__)

def wait_for_element(driver, locator, timeout=10, condition="visible"):
    """
    Waits for an element based on the condition and returns it.
    Supported conditions: 'visible', 'clickable'
    """
    try:
        if condition == "visible":
            return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
        elif condition == "clickable":
            return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
        else:
            raise ValueError(f"Unsupported condition: {repr(condition)}")
    except Exception as e:
        timestamp = int(time.time())
        screenshot_path = f"screenshots/wait_error_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logger.error(f"Element not found: {repr(locator)} | Error: {repr(e)}")
        logger.info(f"Screenshot saved to: {screenshot_path}")
        raise