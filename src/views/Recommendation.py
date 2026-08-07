import streamlit as st

st.title("Recommendation for CompanyX ✅")

with st.container(width=1200, height=400):
    st.write("""
### Key Recommendations

**Customer Segmentation**

- **Champions:** Small group but highest spending → create VIP/loyalty programs and personalized offers.
- **Potential Loyalists:** Largest group but lower spending → focus on upselling, cross-selling, and increasing transaction frequency.
- **At Risk:** Spending is declining → run win-back campaigns with discounts or cashback.
- **Lost:** Low spending → use low-cost reactivation campaigns and stop investing if they do not respond.

**Transaction & Product Behaviour**

- Grocery, Food Stores, and Service Stations are the top MCCs → offer cashback/rewards through these merchants.
- Online transactions have the highest-value outliers → strengthen online fraud detection.
- Most transactions are below $100, while large transactions are rare → optimize for small transactions and monitor unusual high-value transactions.

**Growth Trends**

- Transaction value grew steadily until around 2015, then plateaued → focus on acquiring new customers and expanding products.

**Data Quality**

- `transactions.errors` has ~98% missing data and `zip/merchant_state` ~12% → improve data collection, especially transaction error logs, for better fraud analysis.
""")