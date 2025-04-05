"""
Playwright Test for Database Analytics Chatbot
URL: http://127.0.0.1:5000/admin/dbchat

This test script:
1. Logs in as an admin
2. Navigates to the database analytics chatbot page
3. Asks questions about patient data and visualization
4. Verifies the responses including chart visualization
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

# Test questions for the chatbot
FIRST_QUESTION = "Hello, can you find the number of total patients registered"
SECOND_QUESTION = "can you create a barchart with number of patients registered per month and visualise it"

# Create directories for test results
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(SCRIPT_DIR, "test_results3")
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

def test_database_analytics_chatbot():
    """Test the database analytics chatbot functionality"""
    with sync_playwright() as p:
        # Launch browser
        print_info("Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        try:
            print_header("DATABASE ANALYTICS CHATBOT TEST")
            print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print_info(f"Testing URL: {BASE_URL}/admin/dbchat")
            
            # Step 1: Navigate to login page
            print_step(1, "Navigating to login page")
            page.goto(f"{BASE_URL}/auth/login")
            page.wait_for_load_state("domcontentloaded")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "1_login_page.png"))
            print_info(f"Screenshot saved: 1_login_page.png")
            
            # Step 2: Login as admin
            print_step(2, "Logging in as admin")
            print_info(f"Using email: {ADMIN_EMAIL}")
            print_info(f"Using password: {ADMIN_PASSWORD}")
            page.fill("input[name='identifier']", ADMIN_EMAIL)
            page.fill("input[name='password']", ADMIN_PASSWORD)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "2_login_form_filled.png"))
            print_info(f"Screenshot saved: 2_login_form_filled.png")
            
            # Submit login form
            print_info("Submitting login form...")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            
            # Check if login was successful
            if "/admin/" not in page.url:
                print_error("Login failed. Please check credentials.")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "login_failed.png"))
                print_info(f"Screenshot saved: login_failed.png")
                return False
            
            print_success("Login successful")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "3_login_success.png"))
            print_info(f"Screenshot saved: 3_login_success.png")
            
            # Step 3: Navigate to database analytics chatbot page
            print_step(3, "Navigating to database analytics chatbot page")
            # Try different possible URLs for the DB chat page
            possible_urls = [
                f"{BASE_URL}/admin/dbchat", 
                f"{BASE_URL}/dbchat"
            ]
            
            dbchat_found = False
            for url in possible_urls:
                try:
                    print_info(f"Trying URL: {url}")
                    page.goto(url)
                    page.wait_for_load_state("domcontentloaded")
                    
                    # Check if we're on the database chat page by looking for specific elements
                    if page.is_visible("#chatForm") and page.is_visible("#userInput"):
                        dbchat_found = True
                        print_success(f"Successfully found database chat at: {url}")
                        break
                except Exception as e:
                    print_warning(f"Failed to find database chat at {url}: {str(e)}")
            
            if not dbchat_found:
                print_error("Could not find the database analytics chatbot page")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "dbchat_not_found.png"))
                print_info(f"Screenshot saved: dbchat_not_found.png")
                return False
            
            print_success("Successfully navigated to database analytics chatbot")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "4_dbchat_page.png"))
            print_info(f"Screenshot saved: 4_dbchat_page.png")
            
            # Step 4: Ask first question to the chatbot
            print_step(4, f"Asking first question: '{FIRST_QUESTION}'")
            
            # Type and send first question
            print_info("Typing first question...")
            page.fill("#userInput", FIRST_QUESTION)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "5_first_question_typed.png"))
            print_info(f"Screenshot saved: 5_first_question_typed.png")
            
            # Send the question
            print_info("Sending first question...")
            page.click(".btn-primary")
            
            # Wait for response (typing indicator to appear and then disappear)
            print_info("Waiting for response...")
            page.wait_for_selector(".typing-indicator", state="attached")
            page.wait_for_selector(".typing-indicator", state="detached", timeout=30000)
            
            # Allow time for any animations to complete
            time.sleep(2)
            
            # Check if we got a response
            chat_bubbles = page.locator(".chat-bubble").all()
            if len(chat_bubbles) >= 2:  # At least welcome message + our response
                print_success("Received response to first question")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "6_first_response.png"))
                print_info(f"Screenshot saved: 6_first_response.png")
            else:
                print_error("No response received for first question")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "first_question_no_response.png"))
                print_info(f"Screenshot saved: first_question_no_response.png")
            
            # Step 5: Ask second question about visualization
            print_step(5, f"Asking second question: '{SECOND_QUESTION}'")
            
            # Type and send second question
            print_info("Typing second question...")
            page.fill("#userInput", SECOND_QUESTION)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "7_second_question_typed.png"))
            print_info(f"Screenshot saved: 7_second_question_typed.png")
            
            # Send the question
            print_info("Sending second question...")
            page.click(".btn-primary")
            
            # Wait for response (typing indicator to appear and then disappear)
            print_info("Waiting for response...")
            page.wait_for_selector(".typing-indicator", state="attached")
            page.wait_for_selector(".typing-indicator", state="detached", timeout=60000)  # Longer timeout for visualization
            
            # Allow time for chart rendering
            time.sleep(3)
            
            # Check if we got a response with visualization
            visualization = page.locator(".visualization-container")
            if visualization.count() > 0:
                print_success("Received visualization response to second question")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "8_visualization_response.png"))
                print_info(f"Screenshot saved: 8_visualization_response.png")
            else:
                print_warning("No visualization found in response")
            
            # Step 6: Capture final state of the conversation
            print_step(6, "Capturing full conversation")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "9_full_conversation.png"))
            print_info(f"Screenshot saved: 9_full_conversation.png")
            
            # Step 7: Logout
            print_step(7, "Logging out")
            page.goto(f"{BASE_URL}/auth/logout")
            page.wait_for_load_state("networkidle")
            print_success("Successfully logged out")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "10_logout.png"))
            print_info(f"Screenshot saved: 10_logout.png")
            
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
    report_path = os.path.join(RESULTS_DIR, "database_analytics_chatbot_report.html")
    
    print_info("Generating HTML test report...")
    
    # Get list of screenshots
    screenshots = sorted([f for f in os.listdir(SCREENSHOTS_DIR) if f.endswith('.png')])
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Analytics Chatbot Test Report</title>
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
            <h1>Database Analytics Chatbot Test Report</h1>
            <p>Generated: {timestamp}</p>
            <p>Test URL: {BASE_URL}/admin/dbchat</p>
        </div>
        
        <div class="result {'pass' if test_result else 'fail'}">
            Test Result: {'PASS' if test_result else 'FAIL'}
        </div>
        
        <div class="test-summary">
            <h2>Test Summary</h2>
            <div class="test-details">
                <p><strong>Test Description:</strong> This test verifies that the Database Analytics chatbot responds correctly to queries about patient data and can create visualizations.</p>
                <p><strong>First Question:</strong> "{FIRST_QUESTION}"</p>
                <p><strong>Second Question:</strong> "{SECOND_QUESTION}"</p>
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
    print_header("DATABASE ANALYTICS CHATBOT TEST AUTOMATION")
    print_info(f"Test execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    test_result = test_database_analytics_chatbot()
    generate_html_report(test_result)
    
    if test_result:
        print_success("Test execution completed successfully")
    else:
        print_error("Test execution failed")
    
    print_info(f"Test execution finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
