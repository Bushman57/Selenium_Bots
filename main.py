import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 1. Configuration
ENV_ID = '1996647682249662464'  # Profile ID from app
API_URL = "http://127.0.0.1"

# 2. Start the profile via API to get the debug port
# MoreLogin requires a POST request with the envId in JSON format
payload = {"envId": ENV_ID}
response = requests.post(API_URL, json=payload).json()

if response.get('code') == 0:
    debug_port = response['data']['debugPort']
    #3. Connect Selenium to the dynamic debug port
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")

    browser = webdriver.Chrome()  # Initialize the Chrome browser
    browser.get('https://yoda-ai.onrender.com/')
    browser.maximize_window()  # Maximize the browser window

    title = browser.title  # Get the title of the page

    print(title)  # Print the title to the console
else:
    print(f"Error starting profile: {response.get('msg')}")