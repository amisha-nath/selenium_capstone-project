from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LoginPage:
    """
    Sauce Demo login page object (no By import).
    """

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

        # Locators using string strategies
        self.username_input = ("id", "user-name")
        self.password_input = ("id", "password")
        self.login_button   = ("id", "login-button")
        self.error_message  = ("css selector", "h3[data-test='error']")
        self.inventory_container = ("id", "inventory_container")

    def enter_username(self, username: str):
        elem = self.wait.until(EC.presence_of_element_located(self.username_input))
        elem.clear()
        elem.send_keys(username)

    def enter_password(self, password: str):
        elem = self.wait.until(EC.presence_of_element_located(self.password_input))
        elem.clear()
        elem.send_keys(password)

    def click_login(self):
        self.wait.until(EC.element_to_be_clickable(self.login_button)).click()

    def login(self, username: str, password: str):
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def get_error_message(self) -> str:
        try:
            return self.wait.until(EC.visibility_of_element_located(self.error_message)).text
        except Exception:
            return ""

    def is_login_button_displayed(self) -> bool:
        try:
            return self.wait.until(EC.presence_of_element_located(self.login_button)).is_displayed()
        except Exception:
            return False