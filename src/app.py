from model.AttitudeAnalysis import AttitudeAnalysis
import streamlit as st

@st.cache_resource(show_spinner="data processing...")
def get_analyzer():
    analyzer = AttitudeAnalysis()
    analyzer.run()
    return analyzer

st.session_state.analyzer = get_analyzer()

pg = st.navigation([
    st.Page("views/Dashboard.py", title="Dashboard", icon="📊"),
    st.Page("views/Analytics.py", title="Analytics", icon="📈"),
    st.Page("views/Recommendation.py",title= "Recommendation", icon="✅")
])

pg.run()