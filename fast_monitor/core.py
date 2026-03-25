from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Event
from typing import Callable, Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

FAST_URL = "https://fast.com/"


class MonitorStopped(Exception):
    """Raised when stop_event is set during a run."""


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def default_log_path() -> Path:
    return get_base_dir() / "speed_readings.txt"


@dataclass
class MonitorConfig:
    num_runs: int = 6
    interval_sec: int = 600
    headless: bool = False
    minimized: bool = False
    log_file: Optional[Path] = None
    wait_spinner_sec: int = 180
    wait_speed_text_sec: int = 60
    show_toast: bool = True

    def resolved_log_file(self) -> Path:
        return self.log_file if self.log_file is not None else default_log_path()


def append_log(log_file: Path, line: str) -> None:
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)
        if not line.endswith("\n"):
            f.write("\n")


def parse_speed_numeric(speed_text: str) -> Optional[float]:
    m = re.search(r"\d+(?:\.\d+)?", speed_text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def _check_stop(stop_event: Optional[Event]) -> None:
    if stop_event is not None and stop_event.is_set():
        raise MonitorStopped()


def _wait_poll(
    browser: WebDriver,
    predicate: Callable[[WebDriver], bool],
    total_timeout: float,
    stop_event: Optional[Event],
    chunk: float = 2.0,
) -> None:
    deadline = time.monotonic() + total_timeout
    while time.monotonic() < deadline:
        _check_stop(stop_event)
        if predicate(browser):
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(chunk, remaining))
    raise TimeoutException(f"Timed out after {total_timeout}s")


def wait_for_speed_result(
    browser: WebDriver,
    config: MonitorConfig,
    stop_event: Optional[Event] = None,
) -> None:
    def spinner_gone(d: WebDriver) -> bool:
        try:
            els = d.find_elements(By.CSS_SELECTOR, ".spinner")
            if not els:
                return True
            for el in els:
                if el.is_displayed():
                    return False
            return True
        except Exception:
            return False

    _wait_poll(
        browser,
        spinner_gone,
        float(config.wait_spinner_sec),
        stop_event,
    )

    def speed_ready(d: WebDriver) -> bool:
        try:
            el = d.find_element(By.ID, "speed-value")
            return el.is_displayed() and el.text.strip() != ""
        except NoSuchElementException:
            return False

    _wait_poll(
        browser,
        speed_ready,
        float(config.wait_speed_text_sec),
        stop_event,
    )


def read_speed_text(browser: WebDriver) -> str:
    try:
        value = browser.find_element(By.ID, "speed-value").text.strip()
        if value:
            return value
    except NoSuchElementException:
        pass
    el = browser.find_element(
        By.CSS_SELECTOR, ".speed-results-container.succeeded"
    )
    return el.text.strip()


def show_summary_toast(title: str, message: str) -> None:
    try:
        from win10toast import ToastNotifier

        ToastNotifier().show_toast(title, message, duration=10, threaded=False)
    except Exception:
        print(f"{title}: {message}")


def build_driver(headless: bool) -> WebDriver:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
    return webdriver.Chrome(options=opts)


def _sleep_interruptible(
    seconds: int, stop_event: Optional[Event]
) -> None:
    for _ in range(max(0, seconds)):
        _check_stop(stop_event)
        time.sleep(1)


def run_monitor(
    config: MonitorConfig,
    *,
    on_line: Optional[Callable[[str], None]] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
    stop_event: Optional[Event] = None,
) -> None:
    log_path = config.resolved_log_file()

    def emit(msg: str) -> None:
        if on_line:
            on_line(msg)
        else:
            print(msg)

    driver = build_driver(config.headless)
    samples: list[float] = []
    failures = 0

    try:
        driver.get(FAST_URL)
        if config.minimized:
            driver.minimize_window()

        for i in range(config.num_runs):
            _check_stop(stop_event)
            if on_progress:
                on_progress(i + 1, config.num_runs)

            ts = datetime.now(timezone.utc).isoformat()
            try:
                if i > 0:
                    driver.refresh()

                wait_for_speed_result(driver, config, stop_event)
                speed_text = read_speed_text(browser=driver)
                append_log(log_path, f"{ts}\t{speed_text}")
                emit(f"{ts}  {speed_text}")
                n = parse_speed_numeric(speed_text)
                if n is not None:
                    samples.append(n)
            except MonitorStopped:
                emit("Stopped by user.")
                return
            except TimeoutException as e:
                failures += 1
                msg = f"timeout waiting for result: {e}"
                append_log(log_path, f"{ts}\tERROR\t{msg}")
                emit(f"{ts}  ERROR  {msg}")

            if i < config.num_runs - 1:
                try:
                    _sleep_interruptible(config.interval_sec, stop_event)
                except MonitorStopped:
                    emit("Stopped by user.")
                    return

        if samples:
            avg = sum(samples) / len(samples)
            summary = (
                f"Average download: {avg:.1f} Mbps "
                f"({len(samples)} of {config.num_runs} runs)"
            )
            if failures:
                summary += f", {failures} failed"
            emit(summary)
            if config.show_toast:
                show_summary_toast("fast.com summary", summary)
        else:
            summary = f"No successful speed readings ({failures} failed)."
            emit(summary)
            if config.show_toast:
                show_summary_toast("fast.com summary", summary)

    finally:
        driver.quit()
