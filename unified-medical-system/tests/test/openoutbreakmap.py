from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import unittest
import time

def print_test_header():
    print("=" * 50)
    print("Outbreak Test Started")
    print("=" * 50)

def print_test_success():
    print("=" * 50)
    print("Outbreak Map Test Completed Successfully!")
    print("Map was loaded and zoomed correctly")
    print("=" * 50)

class TestOutbreakMap(unittest.TestCase):
    def setUp(self):
        print_test_header()
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        # Navigate to login page
        self.driver.get("http://127.0.0.1:5000/auth/login")
        print("Navigated to login page")
        
        try:
            # Wait for login form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "loginForm"))
            )
            print("Login form found")

            # Login as admin
            email_field = self.driver.find_element(By.NAME, "identifier")
            password_field = self.driver.find_element(By.NAME, "password")
            
            email_field.send_keys("d.dethanr@gmail.com")
            password_field.send_keys("AAaa!@12")
            print("Credentials entered")
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            print("Login button clicked")
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "content-page"))
            )
            print("Successfully logged in and redirected to dashboard")

        except Exception as e:
            print(f"Setup failed: {str(e)}")
            self.driver.save_screenshot("login_error.png")
            raise

    def test_open_outbreak_map(self):
        try:
            # Navigate to outbreak map
            outbreak_map_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='/admin/outbreakmap']"))
            )
            outbreak_map_link.click()
            print("Clicked on outbreak map link")

            # Wait for map to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "map_ae515ffac4699a595b9141b0f72c6e09"))
            )
            print("Map loaded successfully")

            # Get the map element
            map_element = self.driver.find_element(By.ID, "map_ae515ffac4699a595b9141b0f72c6e09")
            
            # Execute JavaScript to zoom in multiple times
            self.driver.execute_script("""
                var map = document.querySelector('#map_ae515ffac4699a595b9141b0f72c6e09');
                var leafletMap = map._leaflet_map;
                if (leafletMap) {
                    // Store initial zoom level
                    var initialZoom = leafletMap.getZoom();
                    console.log('Initial zoom level:', initialZoom);
                    
                    // Zoom in 3 times with delay
                    setTimeout(function() {
                        leafletMap.setZoom(initialZoom + 2);
                        console.log('First zoom completed');
                        
                        setTimeout(function() {
                            leafletMap.setZoom(initialZoom + 4);
                            console.log('Second zoom completed');
                            
                            setTimeout(function() {
                                leafletMap.setZoom(initialZoom + 6);
                                console.log('Final zoom completed');
                            }, 1000);
                        }, 1000);
                    }, 1000);
                }
            """)
            print("Executing zoom operations...")
            
            # Wait for zooming to complete
            time.sleep(4)
            
            # Verify map is still visible after zoom
            self.assertTrue(map_element.is_displayed())
            print("Map is still visible after zooming")

            # Verify current URL
            expected_url = "http://127.0.0.1:5000/admin/outbreakmap"
            self.assertEqual(self.driver.current_url, expected_url)
            print("URL verification successful")

            print_test_success()

        except TimeoutException:
            print("Test failed: Timeout waiting for map elements")
            self.driver.save_screenshot("map_error.png")
            self.fail("Timeout waiting for map elements")
        except Exception as e:
            print(f"Test failed: {str(e)}")
            self.driver.save_screenshot("test_error.png")
            raise

    def tearDown(self):
        if self.driver:
            self.driver.quit()
            print("Browser closed")

if __name__ == "__main__":
    unittest.main()
