from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

#

driver = webdriver.Chrome()  # Initialize the Chrome driver with options
# driver = webdriver.Firefox()  # Initialize the Firefox driver
driver.maximize_window()  # Maximize the driver window
username = 'ediecarrillo36@gmail.com'
password = 'Dreamash01'
login_url = 'https://yoda-ai-theta.vercel.app/'
driver.get(login_url)  # Navigate to the login page

getting_started_button = driver.find_element(By.CLASS_NAME, 'getstarted')  # Find the login button
# getting_started_button = WebDriverWait(driver, 20).until(
#     EC.element_to_be_clickable((By.CLASS_NAME, 'getstarted'))
# )
getting_started_button.click()
time.sleep(5)  # Wait for the page to load (you can adjust the time as needed)

username_field = driver.find_element(By.ID, 'loginEmail')  # Find the username field
password_field = driver.find_element(By.ID, 'loginPassword')  # Find the password field

username_field.send_keys(username)  # Enter the username
password_field.send_keys(password)  # Enter the password

  # Click the login button
login_button = driver.find_element(By.ID, 'signInBtn')  # Find the login button
login_button.click()  # Click the login button
time.sleep(10)  # Wait for the login process to complete
