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

def test_successful_login_and_add_to_cart(driver):
    time.sleep(5)  # Add a 5-second delay
    driver.get("http://127.0.0.1:5000/auth/login")
    
    email_field = driver.find_element(By.NAME, "identifier")
    email_field.send_keys("tomjosebiju@gmail.com")  # Replace with a valid test email

    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys("Tom@345")  # Replace with a valid test password

    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    click_element_safely(driver, login_button)

    WebDriverWait(driver, 10).until(EC.url_changes("http://127.0.0.1:5000/auth/login"))
    print(f"Logged in. Current URL: {driver.current_url}")

    # Wait for the page to load completely
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("Page body loaded")

    # Wait for product cards to be visible
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product-card")))
        print("Product cards found")
    except TimeoutException:
        print("Product cards not found")
        raise

    # Find and click the first "Add to cart" button
    try:
        add_to_cart_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Add to cart"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", add_to_cart_button)
        time.sleep(1)  # Wait for any animations to complete
        
        # Get the initial cart count
        cart_count_element = driver.find_element(By.CSS_SELECTOR, "span.position-absolute.bg-secondary.rounded-circle")
        initial_count = int(cart_count_element.text) if cart_count_element.text else 0
        print(f"Initial cart count: {initial_count}")

        click_element_safely(driver, add_to_cart_button)
        print("Clicked 'Add to cart' button")
    except (TimeoutException, NoSuchElementException) as e:
        print("'Add to cart' button not found")
        print(f"Error: {str(e)}")
        raise

    # Wait for the cart to update
    try:
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, "span.position-absolute.bg-secondary.rounded-circle"),
                str(initial_count + 1)
            )
        )
        print("Cart updated successfully")
    except TimeoutException:
        print("Cart did not update as expected")
    try:
        cart_count_element = driver.find_element(By.CSS_SELECTOR, "span.position-absolute.bg-secondary.rounded-circle")
        current_count = cart_count_element.text
        print(f"Current cart count: {current_count}")
    except NoSuchElementException:
        print("Cart count element not found")
    print("Add to cart test completed")


def check_server_running():
    try:
        response = requests.get("http://127.0.0.1:8000/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def main():
    driver = setup_driver()
    try:
        test_successful_login_and_add_to_cart(driver)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()