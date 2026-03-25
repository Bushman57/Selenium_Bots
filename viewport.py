from selenium import webdriver
from selenium.webdriver.common.by import By
import time

viewwports = [(375, 667), (414, 896), (768, 1024), (1280, 800), (1440, 900), (1920, 1080)]

driver = webdriver.Chrome()  # Initialize the Chrome driver with options
login_url = 'https://yoda-ai-theta.vercel.app/'
driver.get(login_url)  # Navigate to the login page

try: 
    for viewport in viewwports:
        driver.set_window_size(viewport[0], viewport[1])  # Set the window size to the current viewport
        time.sleep(4)  # Wait for the page to adjust to the new viewport size
except Exception as e:
    print(f"An error occurred: {e}")
