from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


PROXY_HOST = "your-proxy-host"
PROXY_PORT = 1080
PROXY_USER = "your-username"
PROXY_PASS = "your-password"

TARGET_URL = "https://example.com"  # replace with your chat moderator platform URL
CHECK_IP_URL = "https://httpbin.org/ip"  # simple endpoint to verify outgoing IP via proxy


def create_driver_with_proxy():
    proxy_url = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

    options = webdriver.ChromeOptions()
    options.add_argument(f"--proxy-server={proxy_url}")

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver


def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def main():
    driver = None
    try:
        driver = create_driver_with_proxy()

        # First: go to IP check site to confirm traffic via proxy (optional but useful)
        driver.get(CHECK_IP_URL)
        wait_for_page_load(driver, 30)
        time.sleep(2)
        print("IP check page title via proxy:", driver.title)

        # Then: navigate to your target site (chat moderator platform)
        driver.get(TARGET_URL)
        wait_for_page_load(driver, 30)

        # Example: wait for body to be present as a basic connectivity check
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Successfully loaded target page via proxy. Title:", driver.title)

        # Keep browser open briefly so you can see it
        time.sleep(5)

    except Exception as e:
        print(f"An error occurred in proxy bot: {e}")
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    main()

