from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import random
import string

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

def generate_random_email():
    # Generate a random string for the email
    random_string = ''.join(random.choices(string.ascii_lowercase, k=8))
    return f"test_{random_string}@example.com"

def print_test_header():
    print("=" * 50)
    print("RESTART: Registration Test")
    print("*" * 20 + "Place TEST" + "*" * 20)
    print("*" * 50)

def print_test_success():
    print("Registration Test successful!")

def test_successful_registration(driver):
    print_test_header()
    driver.get("http://127.0.0.1:5000/patient/register")
    
    # Wait for the registration form to be loaded
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "registerForm"))
        )
        print("Registration form found")
    except TimeoutException:
        print("Registration form not found within timeout")
        raise

    try:
        # Fill in registration details
        name_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        name_field.send_keys("Test User")
        print("Name entered")

        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_field.send_keys(generate_random_email())
        print("Email entered")

        # Select state
        state_select = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "state"))
        ))
        state_select.select_by_value("KA")  # Selecting Karnataka as an example
        print("State selected")

        phone_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "phonenumber"))
        )
        phone_field.send_keys("9876543210")
        print("Phone number entered")

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys("Test@123")
        print("Password entered")

        confirm_password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "confirm_password"))
        )
        confirm_password_field.send_keys("Test@123")
        print("Confirm password entered")

        # Submit the form
        register_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        click_element_safely(driver, register_button)
        print("Register button clicked")

        # Check for error messages
        try:
            error_message = driver.find_element(By.CLASS_NAME, "text-error")
            print(f"Registration error: {error_message.text}")
            return
        except NoSuchElementException:
            pass

        # Wait for redirect to login page
        WebDriverWait(driver, 20).until(
            lambda driver: driver.current_url == "http://127.0.0.1:5000/auth/login"
        )
        print(f"URL changed to: {driver.current_url}")

        # Verify exact URL match
        assert driver.current_url == "http://127.0.0.1:5000/auth/login", \
            f"Unexpected URL after registration: {driver.current_url}"
        print("Successfully redirected to login page")

        # After successful assertion and before the success message check
        print_test_success()

        # Check for success message
        try:
            success_message = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "success"))
            )
            print(f"Success message displayed: {success_message.text}")
        except TimeoutException:
            print("Success message not found")

    except Exception as e:
        print(f"Test failed: {str(e)}")
        print(f"Current URL: {driver.current_url}")
        # Take screenshot on failure
        driver.save_screenshot("registration_error.png")
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
        test_successful_registration(driver)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
