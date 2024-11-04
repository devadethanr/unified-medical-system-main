from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import os

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
    print("RESTART: Medical Record Download Test")
    print("*" * 20 + "Place TEST" + "*" * 20)
    print("*" * 50)

def print_test_success():
    print("*" * 50)
    print("Medical Record Downloaded Successfully!")
    print("*" * 50)

def login(driver):
    driver.get("http://127.0.0.1:5000/auth/login")
    
    try:
        # Wait for login form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginForm"))
        )
        print("Login form found")

        # Fill in credentials
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

        # Click login button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        click_element_safely(driver, login_button)
        print("Login button clicked")

        # Check for error messages
        try:
            error_message = driver.find_element(By.CLASS_NAME, "alert")
            print(f"Login error: {error_message.text}")
            return False
        except NoSuchElementException:
            pass

        # Wait for redirect to dashboard
        WebDriverWait(driver, 20).until(
            lambda driver: driver.current_url == "http://127.0.0.1:5000/patient/dashboard"
        )
        print("Successfully logged in and redirected to dashboard")
        return True

    except Exception as e:
        print(f"Login failed: {str(e)}")
        driver.save_screenshot("login_error.png")
        return False

def test_medical_record_download(driver):
    print_test_header()
    
    # First login
    if not login(driver):
        raise Exception("Login failed")

    try:
        # Navigate to medical records page
        driver.get("http://127.0.0.1:5000/patient/medical_records")
        print("Navigated to medical records page")

        # Wait for medical records to load
        time.sleep(5)  # Allow time for records to load
        
        # Find and click the first download button
        download_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-download"))
        )
        click_element_safely(driver, download_button)
        print("Clicked download button")

        # Wait for download to complete
        time.sleep(5)

        # Check if file was downloaded
        downloads_path = os.path.expanduser("~/Downloads")
        files = os.listdir(downloads_path)
        pdf_files = [f for f in files if f.startswith("medical_record_") and f.endswith(".pdf")]
        
        if pdf_files:
            print("PDF file downloaded successfully")
            print_test_success()
        else:
            raise Exception("PDF file not found in downloads folder")

    except Exception as e:
        print(f"Test failed: {str(e)}")
        print(f"Current URL: {driver.current_url}")
        driver.save_screenshot("download_error.png")
        raise

def check_server_running():
    try:
        response = requests.get("http://127.0.0.1:5000/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def main():
    driver = setup_driver()
    try:
        test_medical_record_download(driver)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
