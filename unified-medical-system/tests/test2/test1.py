"""
Playwright Test for Doctor Profile Edit Functionality
URL: http://127.0.0.1:5000/doctor/edit_profile

This test script:
1. Logs in as a doctor
2. Navigates to the edit profile page
3. Updates the doctor's name
4. Verifies the changes on the doctor's profile page
5. Generates an HTML test report with screenshots
"""
import os
import sys
from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import colorama
from colorama import Fore, Back, Style

# Initialize colorama for colored terminal output
colorama.init(autoreset=True)

# Test configuration
BASE_URL = "http://127.0.0.1:5000"
DOCTOR_EMAIL = "cathy@gmail.com" # Replace with valid doctor email in your system
DOCTOR_PASSWORD = "jj"   # Replace with the correct password
TEST_NAME = "Cathy Test"

# Create directories for test results
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(SCRIPT_DIR, "test_results")
SCREENSHOTS_DIR = os.path.join(RESULTS_DIR, "screenshots")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def print_header(message):
    """Print a formatted header message"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
    print(f"{Fore.CYAN}{Style.BRIGHT}= {message}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")

def print_step(step_num, message):
    """Print a formatted step message"""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}[STEP {step_num}] {message}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}{'-' * 60}")

def print_success(message):
    """Print a success message"""
    print(f"{Fore.GREEN}{Style.BRIGHT}✓ SUCCESS: {message}")

def print_error(message):
    """Print an error message"""
    print(f"{Fore.RED}{Style.BRIGHT}❌ ERROR: {message}")

def print_warning(message):
    """Print a warning message"""
    print(f"{Fore.YELLOW}⚠️ WARNING: {message}")

def print_info(message):
    """Print an info message"""
    print(f"{Fore.BLUE}ℹ️ INFO: {message}")

def test_doctor_profile_edit():
    """Test the doctor edit profile functionality"""
    with sync_playwright() as p:
        # Launch browser
        print_info("Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        try:
            print_header("DOCTOR PROFILE EDIT TEST")
            print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print_info(f"Testing URL: {BASE_URL}/doctor/edit_profile")
            
            # Step 1: Navigate to login page
            print_step(1, "Navigating to login page")
            page.goto(f"{BASE_URL}/auth/login")
            page.wait_for_load_state("domcontentloaded")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "1_login_page.png"))
            print_info(f"Screenshot saved: 1_login_page.png")
            
            # Step 2: Login as doctor
            print_step(2, "Logging in as doctor")
            print_info(f"Using email: {DOCTOR_EMAIL}")
            page.fill("input[name='identifier']", DOCTOR_EMAIL)
            page.fill("input[name='password']", DOCTOR_PASSWORD)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "2_login_form_filled.png"))
            print_info(f"Screenshot saved: 2_login_form_filled.png")
            
            # Submit login form
            print_info("Submitting login form...")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            
            # Check if login was successful
            if "/doctor/" not in page.url:
                print_error("Login failed. Please check credentials.")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "login_failed.png"))
                print_info(f"Screenshot saved: login_failed.png")
                return False
            
            print_success("Login successful")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "3_login_success.png"))
            print_info(f"Screenshot saved: 3_login_success.png")
            
            # Step 3: Navigate to edit profile page
            print_step(3, "Navigating to edit profile page")
            page.goto(f"{BASE_URL}/doctor/edit_profile")
            page.wait_for_load_state("domcontentloaded")
            
            # Verify we're on the correct page
            assert page.url == f"{BASE_URL}/doctor/edit_profile", "Failed to navigate to edit profile page"
            print_success("Successfully navigated to edit profile page")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "4_edit_profile_page.png"))
            print_info(f"Screenshot saved: 4_edit_profile_page.png")
            
            # Step 4: Test updating doctor's name
            print_step(4, "Updating doctor's name")
            
            # Make sure we're on the Personal Information tab
            print_info("Selecting Personal Information tab...")
            page.click("a[href='#personal-information']")
            page.wait_for_selector("#personal-information.active.show")
            
            # Get initial name value for comparison
            name_input = page.locator("input#name")
            initial_name = name_input.input_value() if name_input.is_visible() else "Not visible"
            print_info(f"Initial name: {initial_name}")
            
            # Update name
            if name_input.is_visible():
                name_input.fill("")
                name_input.fill(TEST_NAME)
                print_success(f"Updated name to: {TEST_NAME}")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "5_name_updated.png"))
                print_info(f"Screenshot saved: 5_name_updated.png")
            else:
                print_error("Name field not found")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "name_field_not_found.png"))
                print_info(f"Screenshot saved: name_field_not_found.png")
                return False
            
            # Step 5: Submit the form
            print_step(5, "Submitting form")
            submit_button = page.locator("#personal-information form button[type='submit']")
            
            if submit_button.is_visible():
                submit_button.click()
                page.wait_for_load_state("networkidle")
                print_success("Form submitted")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "6_form_submitted.png"))
                print_info(f"Screenshot saved: 6_form_submitted.png")
            else:
                print_error("Submit button not found")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "submit_button_not_found.png"))
                print_info(f"Screenshot saved: submit_button_not_found.png")
                return False
            
            # Step 6: Verify submission result
            print_step(6, "Verifying submission result")
            
            # Check for success message
            success_message = page.locator(".alert-success")
            if success_message.is_visible():
                print_success(f"Success message: {success_message.text_content()}")
            else:
                print_warning("No success message found")
                
            # Step 7: Navigate to profile page to verify changes
            print_step(7, "Verifying changes on profile page")
            page.goto(f"{BASE_URL}/doctor/profile")
            page.wait_for_load_state("domcontentloaded")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "7_profile_page.png"))
            print_info(f"Screenshot saved: 7_profile_page.png")
            
            # Check if name was updated
            page_content = page.content()
            if TEST_NAME in page_content:
                print_success(f"Name verification: {TEST_NAME} found on profile page")
            else:
                print_error(f"Name verification failed: {TEST_NAME} not found")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "name_verification_failed.png"))
                print_info(f"Screenshot saved: name_verification_failed.png")
                return False
            
            # Step 8: Logout
            print_step(8, "Logging out")
            page.goto(f"{BASE_URL}/auth/logout")
            page.wait_for_load_state("networkidle")
            print_success("Successfully logged out")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "8_logout.png"))
            print_info(f"Screenshot saved: 8_logout.png")
            
            print_header("TEST COMPLETED SUCCESSFULLY!")
            print_info(f"Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
            
        except Exception as e:
            print_error(f"Test failed with error: {str(e)}")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "error.png"))
            print_info(f"Error screenshot saved: error.png")
            return False
            
        finally:
            print_info("Closing browser...")
            context.close()
            browser.close()

def generate_html_report(test_result):
    """Generate a simple HTML test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_path = os.path.join(RESULTS_DIR, "doctor_profile_edit_report.html")
    
    print_info("Generating HTML test report...")
    
    # Get list of screenshots
    screenshots = sorted([f for f in os.listdir(SCREENSHOTS_DIR) if f.endswith('.png')])
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Doctor Profile Edit Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
            .result {{ font-size: 18px; font-weight: bold; margin: 10px 0; }}
            .pass {{ color: green; }}
            .fail {{ color: red; }}
            .screenshot {{ margin: 20px 0; border: 1px solid #ddd; }}
            .screenshot img {{ max-width: 100%; }}
            .screenshot-title {{ background-color: #eee; padding: 5px; }}
            .test-summary {{ margin: 20px 0; }}
            .test-details {{ margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Doctor Profile Edit Test Report</h1>
            <p>Generated: {timestamp}</p>
            <p>Test URL: {BASE_URL}/doctor/edit_profile</p>
        </div>
        
        <div class="result {'pass' if test_result else 'fail'}">
            Test Result: {'PASS' if test_result else 'FAIL'}
        </div>
        
        <div class="test-summary">
            <h2>Test Summary</h2>
            <div class="test-details">
                <p><strong>Test Description:</strong> This test verifies that a doctor can successfully edit their profile information.</p>
                <p><strong>Initial Name:</strong> Doctor's original name</p>
                <p><strong>Updated Name:</strong> {TEST_NAME}</p>
                <p><strong>Test Status:</strong> {'Successful' if test_result else 'Failed'}</p>
                <p><strong>Test Date:</strong> {timestamp}</p>
            </div>
        </div>
        
        <h2>Test Screenshots</h2>
    """
    
    # Add screenshots to report
    for screenshot in screenshots:
        # Clean up screenshot name for display
        screenshot_name = screenshot.replace('.png', '').replace('_', ' ')
        if screenshot_name.startswith(tuple('0123456789')):
            # Extract step number if present
            parts = screenshot_name.split('_', 1)
            if len(parts) > 1:
                screenshot_name = f"Step {parts[0]}: {parts[1]}"
        
        html_content += f"""
        <div class="screenshot">
            <div class="screenshot-title">{screenshot_name}</div>
            <img src="screenshots/{screenshot}" alt="{screenshot_name}">
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    # Write report to file
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    print_success(f"HTML report generated: {report_path}")
    print_info(f"To view the report, open the file in a web browser.")

if __name__ == "__main__":
    print_header("DOCTOR PROFILE EDIT TEST AUTOMATION")
    print_info(f"Test execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    test_result = test_doctor_profile_edit()
    generate_html_report(test_result)
    
    if test_result:
        print_success("Test execution completed successfully")
    else:
        print_error("Test execution failed")
    
    print_info(f"Test execution finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")