"""Prometheus instrumentation for the Customer Segmentation dashboard.

Streamlit cannot serve extra HTTP routes, so the metrics are exposed by
``prometheus_client`` on a separate port (``METRICS_PORT``, default 8000).
Inside Docker the exporter listens on all interfaces (``METRICS_ADDR`` is set
in the Dockerfile) but the port is never published to the host: only
Prometheus on the internal ``devops-net`` network can scrape it. Locally it
defaults to 127.0.0.1.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger(__name__)

CGROUP_ROOT = Path("/sys/fs/cgroup")
# Streamlit uses exceptions for control flow (st.stop / st.rerun); they are not errors.
_SCRIPT_CONTROL_EXCEPTIONS = {"StopException", "RerunException", "ScriptControlException"}

APP_INFO = Gauge("cs_app_info", "Build and runtime information (value is always 1).",
                 ["version", "git_sha", "env"])
DATA_PIPELINE_RUNS = Counter("cs_data_pipeline_runs", "Executions of the load-clean-merge-segment pipeline.",
                             ["status"])
DATA_PIPELINE_DURATION = Gauge("cs_data_pipeline_duration_seconds",
                               "Duration of the most recent data pipeline run.")
DATA_PIPELINE_LAST_SUCCESS = Gauge("cs_data_pipeline_last_success_timestamp_seconds",
                                   "Unix time of the last successful data pipeline run.")
DATASET_ROWS = Gauge("cs_dataset_rows", "Rows (transactions) in the merged master table.")
CUSTOMERS_PER_SEGMENT = Gauge("cs_customers_per_segment", "Customers in each RFM segment.", ["segment"])
FRAUD_RATE = Gauge("cs_fraud_rate_ratio", "Share of transactions labelled as fraud.")
PAGE_VIEWS = Counter("cs_page_views", "Dashboard page renders.", ["page"])
PAGE_ERRORS = Counter("cs_page_errors", "Dashboard page renders that raised an exception.", ["page"])
PAGE_RENDER_SECONDS = Histogram("cs_page_render_seconds", "Time to render a dashboard page.", ["page"],
                                buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120))
CONTAINER_MEMORY_LIMIT = Gauge("cs_container_memory_limit_bytes",
                               "Memory limit of the container (host memory when unlimited).")
CONTAINER_CPU_LIMIT = Gauge("cs_container_cpu_limit_cores",
                            "CPU limit of the container in cores (host CPUs when unlimited).")

# Pre-create label values so rate()/increase() work from the very first failure.
for _status in ("success", "failure"):
    DATA_PIPELINE_RUNS.labels(status=_status)

_server_lock = threading.Lock()
_server_started = False


def metrics_enabled() -> bool:
    return os.getenv("METRICS_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except OSError:
        return None


def read_memory_limit(root: Path = CGROUP_ROOT) -> int | None:
    """Container memory limit in bytes from cgroup v2 or v1, or None if unlimited."""
    value = _read_text(root / "memory.max")  # cgroup v2
    if value is None:
        value = _read_text(root / "memory" / "memory.limit_in_bytes")  # cgroup v1
    if value is None or value == "max":
        return None
    try:
        limit = int(value)
    except ValueError:
        return None
    return None if limit >= 2 ** 60 else limit  # v1 reports "unlimited" as a huge number


def read_cpu_limit(root: Path = CGROUP_ROOT) -> float | None:
    """Container CPU quota in cores from cgroup v2 or v1, or None if unlimited."""
    value = _read_text(root / "cpu.max")  # cgroup v2: "<quota> <period>"
    if value is not None:
        parts = value.split()
        if len(parts) == 2 and parts[0] != "max":
            return int(parts[0]) / int(parts[1])
        return None
    quota = _read_text(root / "cpu" / "cpu.cfs_quota_us")  # cgroup v1
    period = _read_text(root / "cpu" / "cpu.cfs_period_us")
    if quota and period and int(quota) > 0:
        return int(quota) / int(period)
    return None


def _host_memory_bytes() -> int:
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        return 0


def refresh_static_info() -> None:
    """Publish build info and resource limits (called once at start-up)."""
    APP_INFO.labels(
        version=os.getenv("APP_VERSION", "dev"),
        git_sha=os.getenv("GIT_SHA", "unknown"),
        env=os.getenv("APP_ENV", "local"),
    ).set(1)
    CONTAINER_MEMORY_LIMIT.set(read_memory_limit() or _host_memory_bytes())
    CONTAINER_CPU_LIMIT.set(read_cpu_limit() or float(os.cpu_count() or 1))


def start_metrics_server(port: int | None = None, addr: str | None = None) -> bool:
    """Start the exporter once per process. Safe to call on every Streamlit rerun."""
    global _server_started
    if not metrics_enabled():
        return False
    with _server_lock:
        if _server_started:
            return True
        port = int(port if port is not None else os.getenv("METRICS_PORT", "8000"))
        addr = addr or os.getenv("METRICS_ADDR", "127.0.0.1")
        try:
            start_http_server(port, addr=addr)
        except OSError as exc:
            logger.warning("Metrics exporter not started on %s:%s (%s)", addr, port, exc)
            return False
        refresh_static_info()
        _server_started = True
        logger.info("Metrics exporter listening on %s:%s", addr, port)
        return True


@contextmanager
def track_data_pipeline():
    """Time the data pipeline and count successes/failures."""
    start = time.perf_counter()
    try:
        yield
    except Exception:
        DATA_PIPELINE_RUNS.labels(status="failure").inc()
        raise
    finally:
        DATA_PIPELINE_DURATION.set(time.perf_counter() - start)
    DATA_PIPELINE_RUNS.labels(status="success").inc()
    DATA_PIPELINE_LAST_SUCCESS.set_to_current_time()


def record_analysis(analyzer) -> None:
    """Publish business metrics computed by AttitudeAnalysis."""
    df = analyzer.master_df
    if df is None:
        return
    DATASET_ROWS.set(len(df))
    if "is_fraud" in df.columns and len(df):
        FRAUD_RATE.set(float(df["is_fraud"].astype(bool).mean()))
    rfm = getattr(analyzer.segmentation, "rfm_", None)
    if rfm is not None and "segment" in rfm.columns:
        for segment, count in rfm["segment"].value_counts().items():
            CUSTOMERS_PER_SEGMENT.labels(segment=str(segment)).set(int(count))


@contextmanager
def track_page(page: str):
    """Count and time one render of a dashboard page."""
    start = time.perf_counter()
    PAGE_VIEWS.labels(page=page).inc()
    try:
        yield
    except Exception as exc:
        if type(exc).__name__ not in _SCRIPT_CONTROL_EXCEPTIONS:
            PAGE_ERRORS.labels(page=page).inc()
        raise
    finally:
        PAGE_RENDER_SECONDS.labels(page=page).observe(time.perf_counter() - start)
