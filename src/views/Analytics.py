import streamlit as st
from pathlib import Path

st.title("📈 Analytics")

analyzer = st.session_state.analyzer

CHART_DIR = Path(analyzer.chart_dir)

@st.cache_resource(show_spinner="Loading charts...")
def get_chart_paths(_analyzer):
    return _analyzer.generate_charts()

paths = get_chart_paths(analyzer)

# --- Missing values ---
st.subheader("1. Missing Values")
col1, col2 = st.columns(2)
with col1:
    st.image(str(CHART_DIR / "missing_values_before.png"), caption="Before Cleaning")
with col2:
    st.image(str(CHART_DIR / "missing_values.png"), caption="After Cleaning")

# --- Amount distribution ---
st.subheader("2. Transaction Amount Distribution")
st.image(str(CHART_DIR / "amount_distribution.png"))

# --- Spending by channel & card type ---
st.subheader("3. Spending by Channel & Card Type")
col3, col4 = st.columns(2)
with col3:
    st.image(str(CHART_DIR / "spending_by_channel.png"))
with col4:
    st.image(str(CHART_DIR / "spending_by_card_type.png"))

# --- Yearly trend ---
st.subheader("4. Yearly Trend (2010-2018)")
st.image(str(CHART_DIR / "yearly_trend.png"))

# --- Top MCC ---
st.subheader("5. Top Merchant Categories (MCC)")
st.image(str(CHART_DIR / "top_mcc_categories.png"))

# --- Segment distribution & monetary ---
st.subheader("6. Customer Segments")
col5, col6 = st.columns(2)
with col5:
    st.image(str(CHART_DIR / "segment_distribution.png"), caption="Number of Customers")
with col6:
    st.image(str(CHART_DIR / "segment_monetary.png"), caption="Total Spend")