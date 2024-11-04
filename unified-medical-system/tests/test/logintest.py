from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
from selenium.common.exceptions import WebDriverException
import time

def setup_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver

def wait_for_overlay_to_disappear(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".overlay, .modal, .loading"))
        )
    except TimeoutException:
        print("No overlay found or it didn't disappear")

def click_element_safely(driver, element):
    try:
        element.click()
    except ElementClickInterceptedException:
        wait_for_overlay_to_disappear(driver)
        try:
            element.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", element)

def print_test_header():
    print("=" * 50)
    print("RESTART: Login Test")
    print("*" * 20 + "Login Test" + "*" * 20)
    print("*" * 50)

def print_test_success():
    print("Login Test successful!")

def test_successful_login(driver):
    print_test_header()
    driver.get("http://127.0.0.1:5000/auth/login")
    
    # Wait for the login form to be loaded
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginForm"))
        )
        print("Login form found")
    except TimeoutException:
        print("Login form not found within timeout")
        raise

    # Fill in credentials
    try:
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "identifier"))
        )
        email_field.send_keys("janepat@gmail.com")
        print("Email entered")

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys("PPpp!@12")
        print("Password entered")

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        click_element_safely(driver, login_button)
        print("Login button clicked")

        # Check for error messages
        try:
            error_message = driver.find_element(By.CLASS_NAME, "alert")
            print(f"Login error: {error_message.text}")
            return
        except NoSuchElementException:
            pass

        # Wait for URL change with longer timeout
        WebDriverWait(driver, 20).until(
            lambda driver: driver.current_url == "http://127.0.0.1:5000/patient/dashboard"
        )
        print(f"URL changed to: {driver.current_url}")

        # Verify exact URL match
        assert driver.current_url == "http://127.0.0.1:5000/patient/dashboard", \
            f"Unexpected URL after login: {driver.current_url}"
        print("Successfully redirected to patient dashboard")

        # After successful assertion
        print_test_success()

    except Exception as e:
        print(f"Test failed: {str(e)}")
        print(f"Current URL: {driver.current_url}")
        # Take screenshot on failure
        driver.save_screenshot("login_error.png")
        raise

def check_server_running():
    try:
        response = requests.get("http://127.0.0.1:8000/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def main():
    driver = setup_driver()
    try:
        test_successful_login(driver)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()