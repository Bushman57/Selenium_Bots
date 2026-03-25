from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time

browser = webdriver.Firefox()

browser.get("https://www.youtube.com/")
browser.maximize_window()


def wait_for_page_load(browser, timeout=30):
    WebDriverWait(browser, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


try:
    wait_for_page_load(browser, 30)

    # Search
    browser.find_element(By.NAME, "search_query").send_keys("Selenium WebDriver")
    browser.find_element(By.CSS_SELECTOR, "button[title='Search']").click()

    # Wait until at least one result appears
    wait = WebDriverWait(browser, 30)
    wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@id='video-title']")))

    # Collect video titles currently visible (no scrolling)
    video_elements = browser.find_elements(By.XPATH, "//a[@id='video-title']")
    print(f"Found {len(video_elements)} video results initially visible.\n")

    # Only keep the first 10 results (or fewer if less than 10 exist)
    video_elements = video_elements[:10]
    print(f"Processing {len(video_elements)} top results.\n")

    keyword = "Python"
    keyword_count = 0

    for index, elem in enumerate(video_elements, start=1):
        title_text = elem.text.strip()
        video_url = elem.get_attribute("href")

        print(f"{index}. {title_text}")
        print(f"   URL: {video_url}")

        if keyword.lower() in title_text.lower():
            keyword_count += 1

    print(f"\nNumber of titles containing '{keyword}': {keyword_count}")

    # Optional pause
    time.sleep(5)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    browser.quit()