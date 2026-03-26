import os
import random
import string
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

LOGIN_URL = "https://www.linkedin.com/login"
JOBS_URL = "https://www.linkedin.com/jobs/"
WAIT_SEC = 20

# Easy Apply discovery tab (debug-confirmed).
EASY_APPLY_TAB_CSS = "a.jobs-search-discovery-tabs__tab[data-js-discovery-tabs-tab-link='1']"

# Matches HTML aria-label="Show all top job picks for you" on any tag (a, button, etc.).
_ARIA_SHOW_ALL_TOP_JOB_PICKS = "Show all top job picks for you"

# Inner span (LinkedIn may change utility classes on deploy).
_SHOW_ALL_TOP_PICKS_SPAN = (
    f"a[aria-label='{_ARIA_SHOW_ALL_TOP_JOB_PICKS}'] "
    "span._1766c8a3._52e887e2.ce7de1ea._030d77d9._251c64d3._3981b87d._4c2b0178._59ac4257."
    "edf91104._40a16fd0._160a3e6d.daa65bba._75e87476._36b4f195.e2c77b12._64d551e6."
    "c7ed4125.a2609ec0._8c8ccb7f.ffb82d49._26b9b80d._9fbc8a1a"
)


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE lines into os.environ if the key is not already set."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip().strip('"').strip("'")
        if key not in os.environ:
            os.environ[key] = value


def _random_test_email() -> str:
    local = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return f"{local}@test.invalid"


def _random_test_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=18))


def _try_click(driver, candidates: list[tuple[By, str]]) -> bool:
    click_errors = (
        NoSuchElementException,
        ElementClickInterceptedException,
        ElementNotInteractableException,
        StaleElementReferenceException,
    )
    for by, sel in candidates:
        try:
            el = driver.find_element(by, sel)
            if el.is_displayed():
                el.click()
                print(f"Dismissed overlay / cookies via {by} = {sel!r}")
                return True
        except click_errors:
            continue
    return False


def _dismiss_linkedin_overlays(driver, wait: WebDriverWait) -> None:
    """Cookie walls and alerts can hide the login form."""
    time.sleep(1.5)
    cookie_selectors = [
        (By.CSS_SELECTOR, "button[action-type='ACCEPT']"),
        (By.CSS_SELECTOR, "button.artdeco-global-alert__action"),
        (By.XPATH, "//button[contains(., 'Accept cookies')]"),
        (By.XPATH, "//button[contains(., 'Accept')]"),
        (By.XPATH, "//button[contains(., 'Agree')]"),
        (By.CSS_SELECTOR, "[data-control-name='ga-cookie.consent.accept.v4']"),
    ]
    for _ in range(3):
        if _try_click(driver, cookie_selectors):
            time.sleep(1)
        else:
            break


def _switch_to_frame_with_username(driver, wait: WebDriverWait) -> None:
    """If the email field is inside an iframe, switch into it for the rest of login."""
    driver.switch_to.default_content()
    try:
        wait.until(EC.presence_of_element_located((By.ID, "username")))
        return
    except TimeoutException:
        pass
    frames = driver.find_elements(By.CSS_SELECTOR, "iframe")
    for frame in frames:
        driver.switch_to.default_content()
        try:
            driver.switch_to.frame(frame)
        except (NoSuchElementException, StaleElementReferenceException):
            continue
        if driver.find_elements(By.ID, "username") or driver.find_elements(
            By.NAME, "session_key"
        ):
            print("Using login form inside iframe")
            return
        driver.switch_to.default_content()
    driver.switch_to.default_content()


def _first_matching_element(
    driver,
    candidates: list[tuple[By, str]],
    label: str,
    per_try_sec: float = 6.0,
    *,
    condition=EC.element_to_be_clickable,
):
    last: TimeoutException | None = None
    for by, sel in candidates:
        try:
            el = WebDriverWait(driver, per_try_sec).until(condition((by, sel)))
            print(f"{label}: matched {by} = {sel!r}")
            return el
        except TimeoutException as e:
            last = e
    if condition is not EC.presence_of_element_located:
        return _first_matching_element(
            driver, candidates, label, per_try_sec, condition=EC.presence_of_element_located
        )
    raise TimeoutException(f"{label}: no selector matched") from last


def _click_jobs_nav(driver, wait: WebDriverWait, timeout_sec: float = WAIT_SEC) -> None:
    """
    Open Jobs from the global nav. After login, LinkedIn re-renders the header often, so
    element_to_be_clickable can hit StaleElementReferenceException — re-query in a tight loop.
    """
    jobs_locators: list[tuple[By, str]] = [
        (By.CSS_SELECTOR, "header nav li:nth-child(3) button"),
        (By.CSS_SELECTOR, "header nav ul li:nth-child(3) button"),
        (By.CSS_SELECTOR, "nav.global-nav__nav-items li:nth-child(3) button"),
        (By.CSS_SELECTOR, "header nav li:nth-child(4) button"),
        (By.CSS_SELECTOR, "nav.global-nav__nav-items li:nth-child(4) button"),
        (By.CSS_SELECTOR, "header a[href*='/jobs/']"),
        (By.CSS_SELECTOR, "a.global-nav__primary-link[href*='/jobs']"),
    ]
    deadline = time.monotonic() + timeout_sec
    last_err: BaseException | None = None
    while time.monotonic() < deadline:
        driver.switch_to.default_content()
        restart_outer = False
        for by, sel in jobs_locators:
            try:
                for el in driver.find_elements(by, sel):
                    try:
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", el
                        )
                        if el.is_displayed() and el.is_enabled():
                            try:
                                el.click()
                            except ElementClickInterceptedException:
                                driver.execute_script("arguments[0].click();", el)
                            print(f"Clicked Jobs nav via {by} = {sel!r}")
                            return
                    except StaleElementReferenceException:
                        restart_outer = True
                        break
                    except Exception as e:
                        last_err = e
                        continue
                if restart_outer:
                    break
            except Exception as e:
                last_err = e
                continue
        time.sleep(0.35)

    try:
        driver.get(JOBS_URL)
        print(f"Jobs nav: using direct navigation ({JOBS_URL}) after timeout/stale loop")
    except Exception as e:
        raise TimeoutException(
            f"Jobs nav: failed within {timeout_sec}s (url={driver.current_url!r})"
        ) from (last_err or e)


def _click_show_all(driver, wait: WebDriverWait, per_try_sec: float = 10.0) -> None:
    """Top job picks: aria-label on any element, then inner span; else generic 'Show all' text."""
    candidates: list[tuple[By, str]] = [
        (By.CSS_SELECTOR, f"[aria-label='{_ARIA_SHOW_ALL_TOP_JOB_PICKS}']"),
        (By.CSS_SELECTOR, _SHOW_ALL_TOP_PICKS_SPAN),
        (By.CSS_SELECTOR, "[aria-label*='Show all top job picks']"),
        (By.XPATH, "//a[.//span[normalize-space()='Show all']]"),
        (By.XPATH, "//button[.//span[normalize-space()='Show all']]"),
        (By.XPATH, "//span[normalize-space()='Show all']"),
        (By.XPATH, "//*[normalize-space()='Show all']"),
        (By.PARTIAL_LINK_TEXT, "Show all"),
    ]
    last: TimeoutException | None = None
    for by, sel in candidates:
        try:
            el = WebDriverWait(driver, per_try_sec).until(
                EC.presence_of_element_located((by, sel))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            target = el
            tag = el.tag_name.lower()
            if tag == "span":
                for xp in ("./ancestor::a[1]", "./ancestor::button[1]"):
                    try:
                        target = el.find_element(By.XPATH, xp)
                        break
                    except NoSuchElementException:
                        continue
            WebDriverWait(driver, per_try_sec).until(EC.element_to_be_clickable(target))
            target.click()
            print(f"Clicked Show all via {by} = {sel!r}")
            return
        except TimeoutException as e:
            last = e
    raise TimeoutException("Show all: no locator matched") from last


def _switch_to_discovery_tabs_context(driver, timeout_sec: float = 45.0) -> None:
    """
    LinkedIn may put discovery tabs in the main document, in iframe[data-testid='interop-iframe'],
    or in another / nested iframe. Find a document that contains the tab strip and focus it.
    """
    end = time.monotonic() + timeout_sec
    last_iframe_count = 0
    while time.monotonic() < end:
        driver.switch_to.default_content()
        if driver.find_elements(By.CSS_SELECTOR, ".jobs-search-discovery-tabs__tab"):
            print("Jobs discovery tabs: using main document (no iframe).")
            return

        iframe_candidates: list[tuple[By, str]] = [
            (By.CSS_SELECTOR, "iframe[data-testid='interop-iframe']"),
            (By.CSS_SELECTOR, "iframe[data-testid*='interop']"),
            (By.XPATH, "//iframe[contains(@src,'jobs')]"),
            (By.CSS_SELECTOR, "iframe"),
        ]
        seen: set[int] = set()
        for by, sel in iframe_candidates:
            for frame in driver.find_elements(by, sel):
                driver.switch_to.default_content()
                try:
                    fid = id(frame)
                    if fid in seen:
                        continue
                    seen.add(fid)
                    driver.switch_to.frame(frame)
                except StaleElementReferenceException:
                    continue
                if driver.find_elements(By.CSS_SELECTOR, ".jobs-search-discovery-tabs__tab"):
                    print(
                        "Jobs discovery tabs: using iframe "
                        f"(selector {by}={sel!r}, src={frame.get_attribute('src')!r})"
                    )
                    return
                for inf in driver.find_elements(By.CSS_SELECTOR, "iframe"):
                    try:
                        driver.switch_to.frame(inf)
                    except StaleElementReferenceException:
                        continue
                    if driver.find_elements(By.CSS_SELECTOR, ".jobs-search-discovery-tabs__tab"):
                        print(
                            "Jobs discovery tabs: using nested iframe "
                            f"(src={inf.get_attribute('src')!r})"
                        )
                        return
                    driver.switch_to.parent_frame()

        last_iframe_count = len(driver.find_elements(By.CSS_SELECTOR, "iframe"))
        time.sleep(0.6)

    driver.switch_to.default_content()
    raise TimeoutException(
        f"Could not find .jobs-search-discovery-tabs__tab in main doc or any iframe "
        f"within {timeout_sec}s (iframe count last pass: {last_iframe_count}), "
        f"url={driver.current_url!r}"
    )


def _switch_to_easy_apply_tab_context(driver, timeout_sec: float = 45.0) -> None:
    """
    Easy Apply uses discovery tab data-js-discovery-tabs-tab-link='1'. SelectorHub path:
    iframe[data-testid='interop-iframe'] first; if missing/slow, fall back to main doc / scan.
    (Ignore dynamic #ember* ids; they change per session.)
    """
    driver.switch_to.default_content()
    interop_wait = min(30.0, max(12.0, timeout_sec * 0.55))
    try:
        frame = WebDriverWait(driver, interop_wait).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "iframe[data-testid='interop-iframe']")
            )
        )
        driver.switch_to.frame(frame)
        WebDriverWait(driver, min(20.0, timeout_sec * 0.45)).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-js-discovery-tabs-tab-link='1']")
            )
        )
        print("Easy Apply context: inside iframe[data-testid='interop-iframe']")
        return
    except TimeoutException:
        driver.switch_to.default_content()
    remaining = max(8.0, timeout_sec - interop_wait)
    _switch_to_discovery_tabs_context(driver, timeout_sec=remaining)


def _click_easy_apply_discovery_tab(driver, timeout_sec: float = WAIT_SEC) -> None:
    """Only the debug-confirmed selector for the Easy Apply discovery tab."""
    el = WebDriverWait(driver, timeout_sec).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, EASY_APPLY_TAB_CSS))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
    el.click()
    print(f"Clicked Easy Apply discovery tab via css selector = {EASY_APPLY_TAB_CSS!r}")


# Credentials: same folder as this script, file named `.env` (optional).
# Example lines: LINKEDIN_USERNAME=you@example.com  and  LINKEDIN_PASSWORD=secret
# Shell / system env vars override values from the file if already set.
_load_dotenv(Path(__file__).resolve().parent / ".env")

driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, WAIT_SEC)
driver.get(LOGIN_URL)
print(f"After load: {driver.current_url!r} title={driver.title!r}")

_dismiss_linkedin_overlays(driver, wait)
_switch_to_frame_with_username(driver, wait)

LOGIN_USERNAME_SELECTORS = [
    (By.ID, "username"),
    (By.NAME, "session_key"),
    (By.CSS_SELECTOR, "input[autocomplete='username']"),
    (By.CSS_SELECTOR, "input[type='email']"),
    (
        By.XPATH,
        "//input[contains(@aria-label,'Email') or contains(@aria-label,'Phone') or contains(@aria-label,'email')]",
    ),
    (By.CSS_SELECTOR, "form input[type='text']"),
    (By.XPATH, "//input[contains(@placeholder,'Email') or contains(@placeholder,'Phone')]"),
    (By.XPATH, "//label[contains(.,'Email') or contains(.,'Phone')]/following::input[1]"),
]

username_el = _first_matching_element(
    driver,
    LOGIN_USERNAME_SELECTORS,
    "Username / email field",
    per_try_sec=12.0,
)

password_el = _first_matching_element(
    driver,
    [
        (By.ID, "password"),
        (By.NAME, "session_password"),
        (By.CSS_SELECTOR, "input[type='password'][name='session_password']"),
        (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
        (By.CSS_SELECTOR, "input[type='password']"),
    ],
    "Password field",
    per_try_sec=12.0,
)

real_user = (os.getenv("LINKEDIN_USERNAME") or "").strip()
real_pass = os.getenv("LINKEDIN_PASSWORD") or ""

if real_user and real_pass:
    test_user = real_user
    test_pass = real_pass
    print(f"Using credentials for user: {test_user!r}")
else:
    test_user = _random_test_email()
    test_pass = _random_test_password()
    print(f"Using random test credentials (expect sign-in to fail): {test_user!r}")
username_el.clear()
username_el.send_keys(test_user)
password_el.clear()
password_el.send_keys(test_pass)

form = password_el.find_element(By.XPATH, "./ancestor::form[1]")
submit_btn = form.find_element(By.CSS_SELECTOR, "button[type='submit']")
wait.until(EC.element_to_be_clickable(submit_btn))
print("Sign-in: button[type='submit'] in password form")
submit_btn.click()
driver.switch_to.default_content()

# Wait for main app chrome (feed or Jobs link visible). May sit on checkpoint/2FA.
WebDriverWait(driver, 45).until(
    EC.any_of(
        EC.url_contains("/feed"),
        EC.presence_of_element_located((By.CSS_SELECTOR, "header nav li:nth-child(3) button")),
        EC.presence_of_element_located((By.CSS_SELECTOR, "header nav li:nth-child(4) button")),
    )
)
print(f"URL after sign-in: {driver.current_url}")

try:
    _click_jobs_nav(driver, wait)
except TimeoutException as exc:
    print(
        f"TimeoutException while opening Jobs: {exc} "
        f"| title={driver.title!r}"
    )
    raise

try:
    WebDriverWait(driver, WAIT_SEC).until(EC.url_contains("/jobs"))
except TimeoutException as exc:
    print(
        f"TimeoutException waiting for /jobs URL: {exc} "
        f"| current={driver.current_url!r}"
    )
    raise
print(f"URL on Jobs: {driver.current_url}")

_click_show_all(driver, wait)
time.sleep(3)

try:
    _switch_to_easy_apply_tab_context(driver, timeout_sec=45.0)
    _click_easy_apply_discovery_tab(driver)
finally:
    driver.switch_to.default_content()

time.sleep(20)
print(f"URL after Show all / Easy Apply tab: {driver.current_url}")
driver.quit()
