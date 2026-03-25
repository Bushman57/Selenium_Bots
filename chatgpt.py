from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time

# PROMPT
prompt = "Write a joke about a cat and a dog and tell the current date and time."

driver = webdriver.Firefox()  # Initialize the Firefox driver
driver.get('https://chatgpt.com/')
driver.maximize_window()  # Maximize the driver window

# Wait for page to be ready and JavaScript to render
print("Waiting for ChatGPT to load... (this may take 15+ seconds)")
print("⚠ You likely need to LOG IN with Google or OpenAI account")
print("   Keeping browser open for 30 seconds to allow authentication...\n")

# Wait for document ready state
def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

try:
    wait_for_page_load(driver, 30)
except:
    print("Page didn't reach 'complete' state, continuing anyway...")

# Give additional time for JavaScript to render
print("Waiting for content to render...")
time.sleep(10)

print("\n=== PAGE DEBUG INFO ===")
print(f"Current URL: {driver.current_url}")
print(f"Page Title: {driver.title}")

# Check if login is visible
login_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Log in')]")
google_signin = driver.find_elements(By.XPATH, "//*[contains(text(), 'Google')]")
print(f"Login elements found: {len(login_elements)}")
print(f"Google sign-in found: {len(google_signin)}")

if login_elements or google_signin:
    print("\n🔴 AUTHENTICATION REQUIRED")
    print("=" * 50)
    print("ChatGPT requires you to log in.")
    print("The browser window is still open - please:")
    print("  1. Click 'Log in' or 'Sign up'")
    print("  2. Complete authentication (Google, Microsoft, or OpenAI)")
    print("  3. Wait for the chat page to fully load")
    print("  4. Return to this terminal and press Enter")
    print("=" * 50)
    input("\n⏳ Press Enter when you've finished logging in... ")
    print("Looking for textarea again...")
    time.sleep(3)

# Save debug files
driver.save_screenshot("chatgpt_debug.png")
print("\n✓ Screenshot saved: chatgpt_debug.png")

with open("chatgpt_debug.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
print("✓ HTML saved: chatgpt_debug.html")

# Try to find textarea
print("\n=== SEARCHING FOR TEXTAREA ===")
all_textareas = driver.find_elements(By.TAG_NAME, "textarea")
print(f"Found {len(all_textareas)} textarea elements")

for i, ta in enumerate(all_textareas):
    print(f"  [{i}] visible={ta.is_displayed()}, placeholder='{ta.get_attribute('placeholder')}'")

if len(all_textareas) > 0:
    print("✓ Textarea found! Using first textarea...")
    textarea = all_textareas[0]
    textarea.send_keys(prompt)
else:
    # Try alternative selectors
    selectors = [
        (By.CSS_SELECTOR, "[contenteditable='true']"),
        (By.XPATH, "//div[@role='textbox']"),
        (By.CSS_SELECTOR, "[data-testid*='textarea']"),
    ]
    
    textarea = None
    for selector_type, selector_value in selectors:
        try:
            print(f"Trying selector: {selector_type}")
            textarea = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((selector_type, selector_value))
            )
            print("✓ Found with alternative selector!")
            textarea.send_keys(prompt)
            break
        except:
            continue
    
    if textarea is None:
        print("❌ Still no textarea found")
        print("This likely means:")
        print("  - You didn't complete login")
        print("  - OpenAI changed the HTML structure")
        print("  - ChatGPT page structure is different")
        driver.close()
        exit(1)


# # If using render and the page takes time to load, you can use WebDriverWait to wait for the login button to be clickable before trying to click it.
# button = WebDriverWait(driver, 50).until(
#     EC.element_to_be_clickable((By.ID, 'composer-submit-button'))
# )

button = driver.find_element(By.ID, 'composer-submit-button')  # Find the login button



button.click()  # Click the prompt button
time.sleep(30)  # Wait for the login process to complete
driver.close()



## First enter with cloudFlare, It shows the login page, but after login, it shows the same login page again. I think it is because of the cloudFlare protection. I will try to bypass it by using a different user agent or by using a different browser.