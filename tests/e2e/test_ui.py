"""Browser tests: open every page of the deployed app like a real user would."""
import os
import re

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

pytestmark = pytest.mark.e2e

EXCEPTION_SELECTOR = '[data-testid="stException"]'


def wait_for_text(driver, timeout, *texts):
    """Streamlit renders asynchronously; wait until every text is on the page."""
    WebDriverWait(driver, timeout, poll_frequency=1).until(
        lambda d: all(text in d.find_element(By.TAG_NAME, "body").text for text in texts)
    )


def wait_for_min_elements(driver, timeout, css, min_count):
    """Wait until at least `min_count` elements match `css`; report the last count on failure."""
    found = []

    def enough(d):
        found[:] = d.find_elements(By.CSS_SELECTOR, css)
        return len(found) >= min_count

    try:
        WebDriverWait(driver, timeout).until(enough)
    except TimeoutException:
        raise AssertionError(
            f"Expected >= {min_count} elements matching {css!r} "
            f"within {timeout}s, but found {len(found)}"
        )
    return found


def assert_no_streamlit_error(driver):
    errors = driver.find_elements(By.CSS_SELECTOR, EXCEPTION_SELECTOR)
    assert not errors, f"Streamlit exception shown on page: {errors[0].text[:500]}"


def test_dashboard_shows_all_sections(driver, app_url, timeout):
    driver.get(app_url + "/")
    wait_for_text(driver, timeout, "Introduction", "1. Missing Value Report",
                  "7. Customer Segment Profile (RFM Scoring)")
    assert_no_streamlit_error(driver)
    assert len(driver.find_elements(By.CSS_SELECTOR, '[data-testid="stDataFrame"]')) >= 7


def test_sidebar_shows_deployed_version(driver, app_url, timeout):
    expected = os.environ.get("E2E_EXPECTED_VERSION")
    if not expected:
        pytest.skip("E2E_EXPECTED_VERSION not set")
    driver.get(app_url + "/")
    wait_for_text(driver, timeout, f"Version {expected}")


def test_analytics_page_renders_every_chart(driver, app_url, timeout):
    driver.get(app_url + "/Analytics")
    wait_for_text(driver, timeout, "Analytics", "6. Customer Segments")
    WebDriverWait(driver, timeout, poll_frequency=1).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, 'img[src*="/media/"]')) >= 9
    )
    assert_no_streamlit_error(driver)


def test_recommendation_page(driver, app_url, timeout):
    driver.get(app_url + "/Recommendation")
    wait_for_text(driver, timeout, "Recommendation for CompanyX", "Key Recommendations", "Customer Segmentation")
    assert_no_streamlit_error(driver)


def test_metrics_prove_version_and_dataset_size(driver, app_url, timeout):
    """The exporter (internal port 8000) must report this build and a dataset of the expected size.

    Staging serves the committed sample; production must serve the full dataset
    from the GitHub Release, so E2E_MIN_DATASET_ROWS is much higher there.
    """
    metrics_url = os.environ.get("E2E_METRICS_URL")
    if not metrics_url:
        pytest.skip("E2E_METRICS_URL not set")
    driver.get(app_url + "/")  # make sure the data pipeline has run
    wait_for_text(driver, timeout, "7. Customer Segment Profile (RFM Scoring)")
    driver.get(metrics_url)
    body = driver.find_element(By.TAG_NAME, "body").text
    expected = os.environ.get("E2E_EXPECTED_VERSION")
    if expected:
        assert f'version="{expected}"' in body
    rows = re.search(r"^cs_dataset_rows ([0-9.e+]+)$", body, re.MULTILINE)
    assert rows, "cs_dataset_rows not exported"
    assert float(rows.group(1)) >= int(os.environ.get("E2E_MIN_DATASET_ROWS", "1"))
