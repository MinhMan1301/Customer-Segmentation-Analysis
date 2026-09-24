import os

import streamlit as st

import telemetry
from model.AttitudeAnalysis import AttitudeAnalysis

# No-op if serve.py already started the exporter or METRICS_ENABLED=false.
telemetry.start_metrics_server()


@st.cache_resource(show_spinner="data processing...")
def get_analyzer():
    with telemetry.track_data_pipeline():
        analyzer = AttitudeAnalysis(chart_dir=os.getenv("CHART_DIR", "charts"))
        analyzer.run()
    telemetry.record_analysis(analyzer)
    return analyzer


st.session_state.analyzer = get_analyzer()
st.sidebar.caption(f"Version {os.getenv('APP_VERSION', 'dev')} · {os.getenv('APP_ENV', 'local')}")

pg = st.navigation([
    st.Page("views/Dashboard.py", title="Dashboard", icon="📊"),
    st.Page("views/Analytics.py", title="Analytics", icon="📈"),
    st.Page("views/Recommendation.py", title="Recommendation", icon="✅"),
])

with telemetry.track_page(pg.title):
    pg.run()
