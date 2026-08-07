import streamlit as st

st.title("💡 Introduction")

analyzer = st.session_state.analyzer   # dùng lại, không gọi run() nữa

st.subheader("1. Missing Value Report")
st.dataframe(analyzer.eda.missing_value_report())

st.subheader("2. Spending Overview")
st.dataframe(analyzer.eda.spending_overview())

st.subheader("3. Spending by Transaction Channel")
st.dataframe(analyzer.eda.spending_by_channel())

st.subheader("4. Spending by Card Type")
st.dataframe(analyzer.eda.spending_by_card_type())

st.subheader("5. Yearly Trend (2010-2019)")
st.dataframe(analyzer.eda.yearly_trend())

st.subheader("6. Top Merchant Categories (MCC)")
st.dataframe(analyzer.eda.top_mcc_categories())

st.subheader("7. Customer Segment Profile (RFM Scoring)")
st.dataframe(analyzer.segmentation.segment_profile())