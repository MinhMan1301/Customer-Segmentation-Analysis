import os
from types import SimpleNamespace

import pandas as pd
import pytest
from prometheus_client import REGISTRY

import telemetry


def value(name, **labels):
    return REGISTRY.get_sample_value(name, labels) or 0.0


def test_track_data_pipeline_counts_success_and_failure():
    ok_before = value("cs_data_pipeline_runs_total", status="success")
    fail_before = value("cs_data_pipeline_runs_total", status="failure")
    with telemetry.track_data_pipeline():
        pass
    with pytest.raises(RuntimeError):
        with telemetry.track_data_pipeline():
            raise RuntimeError("boom")
    assert value("cs_data_pipeline_runs_total", status="success") == ok_before + 1
    assert value("cs_data_pipeline_runs_total", status="failure") == fail_before + 1
    assert value("cs_data_pipeline_last_success_timestamp_seconds") > 0


def test_record_analysis_publishes_business_metrics(analysis):
    telemetry.record_analysis(analysis)
    assert value("cs_dataset_rows") == len(analysis.master_df)
    assert 0 <= value("cs_fraud_rate_ratio") <= 1
    counts = analysis.segmentation.rfm_["segment"].value_counts()
    for segment, count in counts.items():
        assert value("cs_customers_per_segment", segment=segment) == count


def test_record_analysis_ignores_unrun_analyzer():
    telemetry.record_analysis(SimpleNamespace(master_df=None))


def test_track_page_counts_views_errors_and_ignores_streamlit_control_flow():
    class RerunException(Exception):
        pass

    views = value("cs_page_views_total", page="T")
    with telemetry.track_page("T"):
        pass
    with pytest.raises(ValueError):
        with telemetry.track_page("T"):
            raise ValueError("render failed")
    with pytest.raises(RerunException):
        with telemetry.track_page("T"):
            raise RerunException()
    assert value("cs_page_views_total", page="T") == views + 3
    assert value("cs_page_errors_total", page="T") == 1
    assert value("cs_page_render_seconds_count", page="T") == 3


def test_metrics_server_is_disabled_in_tests():
    assert telemetry.metrics_enabled() is False
    assert telemetry.start_metrics_server() is False


def test_metrics_server_starts_once(monkeypatch):
    calls = []
    monkeypatch.setenv("METRICS_ENABLED", "true")
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    monkeypatch.setattr(telemetry, "_server_started", False)
    monkeypatch.setattr(telemetry, "start_http_server", lambda port, addr: calls.append((port, addr)))
    assert telemetry.start_metrics_server() is True
    assert telemetry.start_metrics_server() is True
    assert calls == [(8000, "127.0.0.1")]
    assert value("cs_app_info", version="9.9.9", git_sha="unknown", env="local") == 1
    assert value("cs_container_cpu_limit_cores") > 0
    if hasattr(os, "sysconf"):  # Linux/containers only; Windows has no sysconf, so the gauge stays 0 there
        assert value("cs_container_memory_limit_bytes") > 0


def test_metrics_server_port_in_use_is_not_fatal(monkeypatch):
    def busy(port, addr):
        raise OSError("address already in use")

    monkeypatch.setenv("METRICS_ENABLED", "1")
    monkeypatch.setattr(telemetry, "_server_started", False)
    monkeypatch.setattr(telemetry, "start_http_server", busy)
    assert telemetry.start_metrics_server(port=1234) is False


@pytest.mark.parametrize("files, memory, cpu", [
    ({"memory.max": "1073741824", "cpu.max": "200000 100000"}, 1073741824, 2.0),
    ({"memory.max": "max", "cpu.max": "max 100000"}, None, None),
    ({"memory/memory.limit_in_bytes": "536870912", "cpu/cpu.cfs_quota_us": "50000",
      "cpu/cpu.cfs_period_us": "100000"}, 536870912, 0.5),
    ({"memory/memory.limit_in_bytes": str(2 ** 63), "cpu/cpu.cfs_quota_us": "-1",
      "cpu/cpu.cfs_period_us": "100000"}, None, None),
    ({"memory.max": "garbage"}, None, None),
    ({}, None, None),
])
def test_cgroup_limits(tmp_path, files, memory, cpu):
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    assert telemetry.read_memory_limit(tmp_path) == memory
    assert telemetry.read_cpu_limit(tmp_path) == cpu


def test_fraud_rate_handles_object_dtype():
    df = pd.DataFrame({"is_fraud": pd.Series([True, False, False, False], dtype=object)})
    telemetry.record_analysis(SimpleNamespace(master_df=df, segmentation=SimpleNamespace(rfm_=None)))
    assert value("cs_fraud_rate_ratio") == 0.25