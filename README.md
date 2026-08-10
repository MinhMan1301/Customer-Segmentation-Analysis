# 💳 Customer Transaction Analysis & Segmentation

A Streamlit data app that analyzes Company X's customer transaction data and segments customers using **RFM scoring**, turning raw transaction, card, and user data into actionable business recommendations.

---

## 🌐 Overview

Company X provides financial products and services to individual customers and holds a large volume of customer transaction data. This project processes that data end-to-end — from raw CSVs to a live, interactive dashboard — to help Company X understand customer behavior, segment its customer base, and act on the findings.

### 🎯 Project Objectives
- **Understand Customer Behavior** — explore transaction patterns and trends across the dataset.
- **Build Customer Segments** — group customers with RFM (Recency, Frequency, Monetary) scoring.
- **Analyze Behavior per Segment** — profile each segment's spending and demographics.
- **Recommend Actions** — propose targeted strategies for each customer segment.

---

## 🚀 Key Features

### 🔒 Core Functionalities
- **Automated Data Pipeline** — load, clean, and merge 5 raw datasets into one analysis-ready table.
- **Exploratory Data Analysis (EDA)** — missing-value reporting, spending overview, channel/card-type breakdowns, yearly trends, top merchant categories.
- **RFM Customer Segmentation** — quantile-based scoring into 5 segments: Champions, Loyal Customers, Potential Loyalists, At Risk, Lost.
- **Interactive Dashboard** — 3-page Streamlit app (Dashboard, Analytics, Recommendation) for exploring results without touching code.

### 🌟 Highlighted Features
- **Before/After Cleaning Comparison** — visualizes missing-value ratios pre- and post-cleaning, directly from the raw tables.
- **Segment Profiling** — average recency, frequency, monetary value, age, income, and credit score per segment.
- **Business-Ready Recommendations** — concrete actions per segment, grounded in observed spending and MCC (merchant category) patterns.

---

## 🏗️ System Architecture

### 💻 Technology Stack

| Category | Tools | Description |
|---|---|---|
| **Data Processing** | Python, Pandas, NumPy | Cleaning, merging, and numerical feature engineering |
| **Analysis** | Custom `EDA` & `CustomerSegmentation` classes | Spending analysis & RFM scoring |
| **Visualization** | Matplotlib, Seaborn | Static charts rendered into the dashboard |
| **App / UI** | Streamlit | Multi-page interactive dashboard |
| **Version Control** | GitHub | Collaboration and issue tracking |

### 📦 Project Structure

```
model/
├── __init__.py
├── AttitudeAnalysis.py      # Main entry point: load → clean → merge → EDA → segment → visualize
├── DataLoader.py            # Reads the 5 raw CSV files
├── TableCleaner.py          # Cleans each raw table individually
├── Merger.py                # Merges cleaned tables into one master table
├── EDA.py                   # Answers the project's guiding analysis questions
├── CustomerSegmentation.py  # Builds RFM scores and assigns segments
└── Visualizer.py            # Generates and saves all charts

views/
├── Dashboard.py        # EDA tables: missing values, spending, trends, segment profile
├── Analytics.py         # Chart gallery: all Visualizer outputs
└── Recommendation.py   # Business recommendations per segment

app.py                   # Streamlit entry point & page navigation
```

---

## 📊 Dataset

The dataset is a comprehensive financial dataset covering customer transactions, cards, and user profiles from banking institutions over **2010–2019**, made up of 5 tables:

| Table | Description |
|---|---|
| **Transaction Data** | Every transaction: amount, date, channel (Swipe/Chip/Online), merchant, errors |
| **Card Data** | Card brand/type, credit limit, chip status, dark-web exposure flag |
| **Merchant Category (MCC) Data** | Merchant category codes and descriptions |
| **Fraud Labels Data** | Whether a transaction was flagged as fraudulent |
| **User Data** | Age, income, debt, credit score, and other demographics |

> ⚠️ **Note:** `transactions_data_25pc.csv` and `train_fraud_labels.csv` are too large to be tracked in this repository (see `.gitignore`). Download the full dataset by contacting me and place all 5 CSVs into a local `data/` folder before running the app or you can see the demo to know more about the app.

---

## 🔄 Data Pipeline

1. **Load** — `DataLoader` reads all 5 CSVs.
2. **Clean** — `TableCleaner` handles each table individually: strips currency symbols, imputes missing values (median for numeric, mode for categorical), casts ID columns to string, parses dates, and derives flags like `is_error` and `is_fraud`.
3. **Merge** — `Merger` joins all tables into one transaction-level master table (`card_id`, `client_id`, and `mcc` as join keys).
4. **Analyze** — `EDA` computes missing-value reports, spending overviews, channel/card-type breakdowns, yearly trends, and top merchant categories.
5. **Segment** — `CustomerSegmentation` builds an RFM table per customer and scores it into 5 segments.
6. **Visualize** — `Visualizer` renders and saves every chart used across the dashboard.

---

## 🧮 RFM Segmentation Methodology

| Metric | Definition |
|---|---|
| **Recency** | Days since a customer's most recent transaction |
| **Frequency** | Total number of transactions per customer |
| **Monetary** | Total amount spent by the customer |

Each metric is scored 1–4 using quantiles, summed into an `RFM_score`, and mapped to a segment:

| RFM Score | Segment |
|---|---|
| 10–12 | Champions |
| 8–9 | Loyal Customers |
| 6–7 | Potential Loyalists |
| 4–5 | At Risk |
| 0–3 | Lost |

---

## 💡 Key Recommendations

- **Champions** — small but highest-spending group → VIP/loyalty programs and personalized offers.
- **Potential Loyalists** — largest group, lower spending → upselling, cross-selling, increase transaction frequency.
- **At Risk** — declining spend → win-back campaigns with discounts or cashback.
- **Lost** — low spend → low-cost reactivation only; stop investing if unresponsive.
- Grocery, Food Stores, and Service Stations are the top merchant categories → cashback/rewards partnerships through these merchants.
- Online transactions have the highest-value outliers → strengthen online fraud detection.
- Transaction value grew steadily until ~2015 then plateaued → prioritize new customer acquisition and product expansion.

---

## 🛠️ Tools Used

- **[Streamlit](https://streamlit.io/)** — multi-page interactive dashboard (Dashboard, Analytics, Recommendation)
- **[Pandas](https://pandas.pydata.org/)** — data loading, cleaning, merging, and aggregation
- **[NumPy](https://numpy.org/)** — underlying numerical operations for Pandas computations
- **[Matplotlib](https://matplotlib.org/)** — chart rendering engine
- **[Seaborn](https://seaborn.pydata.org/)** — statistical visualizations (histograms, boxplots, bar/count plots)

---

## ▶️ How to Run

```bash
pip install streamlit pandas numpy matplotlib seaborn
streamlit run app.py
```

1. Download the dataset by contacting me.
2. Place all 5 CSVs (`transactions_data_25pc.csv`, `cards_data.csv`, `users_data.csv`, `mcc_codes.csv`, `train_fraud_labels.csv`) into a `data/` directory one level above the `model/` package — or pass a custom path via `AttitudeAnalysis(data_dir=...)`.
3. Run `streamlit run app.py`.

---

## 🎥 Video Demo

[[**Video Demo: Blood System Management Website**]([anaalysis.webm](https://github.com/user-attachments/assets/04c682ac-4416-4122-960d-723fa28fb642)
)](https://github.com/user-attachments/assets/04c682ac-4416-4122-960d-723fa28fb642)

---

## 📬 Contact

**Author:** _[MinhMan1301]_
📧 Email: [phamminhman13012005@gmail.com](mailto:phamminhman13012005@gmail.com)
🔗 GitHub: [MinhMan1301](https://github.com/MinhMan1301)
🔗 LinkedIn: [NGUYEN MINH MAN PHAM](https://www.linkedin.com/in/nguyen-minh-man-pham-47b493311/)
