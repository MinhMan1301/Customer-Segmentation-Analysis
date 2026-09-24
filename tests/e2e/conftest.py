"""Selenium fixtures for browser tests against a deployed environment.

Configured by ci/e2e.sh through environment variables:
    E2E_APP_URL        e.g. http://cs-staging-app:8501
    E2E_SELENIUM_URL   e.g. http://cs-selenium-42:4444/wd/hub
    E2E_TIMEOUT        seconds to wait for the data pipeline (first load)
    E2E_EXPECTED_VERSION  version shown in the sidebar (optional)
    E2E_ARTIFACT_DIR   where screenshots are written
"""
import os
from pathlib import Path

import pytest
from selenium import webdriver

APP_URL = os.environ.get("E2E_APP_URL", "http://localhost:8501").rstrip("/")
SELENIUM_URL = os.environ.get("E2E_SELENIUM_URL", "http://localhost:4444/wd/hub")
TIMEOUT = int(os.environ.get("E2E_TIMEOUT", "180"))
ARTIFACT_DIR = Path(os.environ.get("E2E_ARTIFACT_DIR", "reports/e2e"))


@pytest.fixture(scope="session")
def app_url():
    return APP_URL


@pytest.fixture(scope="session")
def timeout():
    return TIMEOUT


@pytest.fixture(scope="session")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-dev-shm-usage")
    browser = webdriver.Remote(command_executor=SELENIUM_URL, options=options)
    browser.set_page_load_timeout(TIMEOUT)
    yield browser
    browser.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Save a screenshot for every e2e test (evidence for the report), named by outcome."""
    outcome = yield
    report = outcome.get_result()
    browser = item.funcargs.get("driver") if hasattr(item, "funcargs") else None
    if report.when == "call" and browser is not None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        status = "FAILED" if report.failed else "passed"
        browser.save_screenshot(str(ARTIFACT_DIR / f"{item.name}-{status}.png"))
