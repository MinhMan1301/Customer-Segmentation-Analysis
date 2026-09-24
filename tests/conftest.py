"""Shared fixtures. Tests never need the real (large) dataset."""
import os

# Must be set before `telemetry` is imported anywhere: tests never bind ports.
os.environ.setdefault("METRICS_ENABLED", "false")
os.environ.setdefault("MPLBACKEND", "Agg")

import pytest  # noqa: E402

from data_factory import make_raw_tables, write_dataset  # noqa: E402
from model.AttitudeAnalysis import AttitudeAnalysis  # noqa: E402


@pytest.fixture(scope="session")
def raw_tables_cache():
    return make_raw_tables()


@pytest.fixture()
def raw(raw_tables_cache):
    """Fresh copies of the synthetic raw tables (safe to mutate)."""
    return {name: df.copy() for name, df in raw_tables_cache.items()}


@pytest.fixture(scope="session")
def data_dir(tmp_path_factory):
    return write_dataset(tmp_path_factory.mktemp("data"))


@pytest.fixture(scope="session")
def analysis(data_dir, tmp_path_factory):
    """A fully executed AttitudeAnalysis on the synthetic dataset."""
    analyzer = AttitudeAnalysis(data_dir=data_dir, chart_dir=str(tmp_path_factory.mktemp("charts")))
    analyzer.run()
    return analyzer
