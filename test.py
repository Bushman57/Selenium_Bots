from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

driver = webdriver.Firefox()  # Initialize the Firefox driver
driver.get('https://yoda-ai.onrender.com/')
driver.maximize_window()  # Maximize the driver window

title = driver.title  # Get the title of the page

print(title)  # Print the title to the console

# If using render and the page takes time to load, you can use WebDriverWait to wait for the login button to be clickable before trying to click it.
button = WebDriverWait(driver, 50).until(
    EC.element_to_be_clickable((By.CLASS_NAME, 'getstarted'))
)

# button = driver.find_element(By.CLASS_NAME, 'getstarted')  # Find the login button



button.click()  # Click the login button
driver.close()