"""Streamlit AppTest: renders the real pages headlessly (no browser needed)."""
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.integration

SRC = Path(__file__).resolve().parents[2] / "src"


def run_view(name, analyzer):
    at = AppTest.from_file(str(SRC / "views" / f"{name}.py"), default_timeout=120)
    at.session_state["analyzer"] = analyzer
    return at.run()


def test_dashboard_renders_seven_tables(analysis):
    at = run_view("Dashboard", analysis)
    assert not at.exception
    assert len(at.subheader) == 7
    assert len(at.dataframe) == 7


def test_analytics_renders_all_charts(analysis):
    at = run_view("Analytics", analysis)
    assert not at.exception
    assert [h.value for h in at.subheader][-1] == "6. Customer Segments"
    assert len(at.get("image")) == 9


def test_recommendation_page(analysis):
    at = run_view("Recommendation", analysis)
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    for segment in ("Champions", "Potential Loyalists", "At Risk", "Lost"):
        assert segment in text


def test_entrypoint_runs_pipeline_and_navigation(data_dir, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("CHART_DIR", str(tmp_path))
    monkeypatch.setenv("APP_VERSION", "1.0.42")
    st.cache_resource.clear()
    at = AppTest.from_file(str(SRC / "app.py"), default_timeout=180).run()
    assert not at.exception
    assert at.title[0].value.endswith("Introduction")
    assert at.sidebar.caption[0].value.startswith("Version 1.0.42")
    at.switch_page("views/Recommendation.py").run()
    assert not at.exception
    assert "Recommendation" in at.title[0].value
