# 💳 Customer Transaction Analysis & Segmentation

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.64-FF4B4B?logo=streamlit&logoColor=white)
![Jenkins](https://img.shields.io/badge/CI%2FCD-Jenkins%207%20stages-D24939?logo=jenkins&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![SonarQube](https://img.shields.io/badge/Quality%20Gate-Passed-4E9BCD?logo=sonarqube&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-96%25-brightgreen)
![Prometheus](https://img.shields.io/badge/Monitoring-Prometheus%20%2B%20Grafana-E6522C?logo=prometheus&logoColor=white)

A Streamlit data app that analyses Company X's customer transaction data and segments customers using **RFM scoring**, turning 3.3 million raw transactions, card and user records into actionable business recommendations.

The app is shipped through a fully automated **7-stage Jenkins DevOps pipeline**: Build → Test → Code Quality → Security → Deploy → Release → Monitoring. Every push to `main` is built, tested, analysed, scanned, deployed to staging, promoted to production and monitored with alerting, **in about three minutes and with no manual steps**.

---

## 🌐 Overview

Company X provides financial products and services to individual customers and holds a large volume of customer transaction data. This project processes that data end to end, from raw CSVs to a live, interactive dashboard, to help Company X understand customer behaviour, segment its customer base and act on the findings.

### 🎯 Project Objectives
- **Understand customer behaviour**: explore transaction patterns and trends across the dataset.
- **Build customer segments**: group customers with RFM (Recency, Frequency, Monetary) scoring.
- **Analyse behaviour per segment**: profile each segment's spending and demographics.
- **Recommend actions**: propose targeted strategies for each customer segment.
- **Deliver it like production software**: automated testing, quality gates, security scanning, versioned releases, automatic rollback and live monitoring with alerting.

---

## 🚀 Key Features

### 🔒 Core Functionalities
- **Automated data pipeline**: load, clean and merge 5 raw datasets into one analysis-ready table.
- **Exploratory Data Analysis (EDA)**: missing-value reporting, spending overview, channel and card-type breakdowns, yearly trends, top merchant categories.
- **RFM customer segmentation**: quantile-based scoring into 5 segments: Champions, Loyal Customers, Potential Loyalists, At Risk, Lost.
- **Interactive dashboard**: 3-page Streamlit app (Dashboard, Analytics, Recommendation) for exploring results without touching code.

### 🌟 Highlighted Features
- **Before/after cleaning comparison**: missing-value ratios pre- and post-cleaning, computed directly from the raw tables.
- **Segment profiling**: average recency, frequency, monetary value, age, income and credit score per segment.
- **Business-ready recommendations**: concrete actions per segment, grounded in observed spending and MCC (merchant category) patterns.
- **Privacy by design**: card numbers and CVVs are dropped at load time, so they never reach the dashboard, charts, logs or metrics.
- **Built-in observability**: the app exports its own Prometheus metrics (version, dataset size, fraud rate, customers per segment, page render time, memory and CPU against the container limits).

---

## 📌 Pipeline at a Glance

| | Result |
|---|---|
| Stages | **7 / 7**, fully automated, triggered by every push to `main` |
| Duration | about **3 minutes** from `git push` to a monitored production release |
| Tests | **73** unit + integration tests (**96.8 %** coverage, gate 80 %) and **5** Selenium browser tests per environment |
| Code quality | SonarQube **CS Gate passed**: 0 bugs, 0 vulnerabilities, 0.0 % duplication, A ratings |
| Security | Bandit: 0 issues · pip-audit: 0 vulnerable packages · Trivy: 0 critical CVEs · SBOM on every release |
| Releases | Versioned Docker images, Git tags `v<major>.<minor>.<build>` and GitHub Releases |
| Rollback | Automatic in staging and production (verified in real failed builds) |
| Alerting | 7 Prometheus alert rules, e-mail via Alertmanager; incident drill: detected in **55 s**, recovered in **83 s** |

---

## 🏗️ System Architecture

### 💻 Technology Stack

| Category | Tools | Description |
|---|---|---|
| **Data Processing** | Python 3.12, pandas, pyarrow, NumPy | Cleaning, merging and feature engineering; multi-threaded CSV parsing |
| **Analysis** | Custom `EDA` & `CustomerSegmentation` classes | Spending analysis and RFM scoring |
| **Visualisation** | Matplotlib, Seaborn | Static charts rendered into the dashboard |
| **App / UI** | Streamlit | Multi-page interactive dashboard |
| **CI/CD** | Jenkins (Pipeline as Code), Docker, Docker Compose, private Docker registry | Automated build, test, deploy and release |
| **Testing** | pytest, pytest-cov, Streamlit AppTest, Selenium | Unit, integration and end-to-end browser tests |
| **Code Quality** | SonarQube, flake8, hadolint, shellcheck | Quality gate, code smells, duplication, complexity |
| **Security** | Bandit, pip-audit, Trivy | SAST, dependency CVEs, image CVEs, SBOM, secret and misconfiguration scanning |
| **Monitoring** | Prometheus, Alertmanager, Grafana, Blackbox exporter | Metrics, dashboards, e-mail alerts |
| **Version Control** | GitHub (repository, tags, Releases) | Code, versioned releases and dataset hosting |

### 🔁 CI/CD Pipeline

```mermaid
flowchart LR
    push([git push]) --> B[Build<br/>Docker image v1.x.N]
    B --> T[Test<br/>pytest + smoke test]
    T --> Q[Code Quality<br/>SonarQube gate]
    Q --> S[Security<br/>Bandit · pip-audit · Trivy]
    S --> D[Deploy<br/>staging + Selenium]
    D --> R[Release<br/>production + GitHub Release]
    R --> M[Monitoring<br/>Prometheus · Grafana · alerts]
    D -. failure .-> RB1[rollback staging]
    R -. failure .-> RB2[rollback production]
```

| # | Stage | What happens | Gate (fails the build) |
|---|---|---|---|
| 1 | **Build** | Versioned Docker image (`VERSION` + build number), tagged by version and commit, pushed to a local registry; digest recorded in `build-info.json` | build or push error |
| 2 | **Test** | 73 unit & integration tests (incl. every Streamlit page), then a smoke test of the built container | any failing test, coverage < 80 % |
| 3 | **Code Quality** | flake8, hadolint, shellcheck, SonarQube analysis with a custom quality gate ("CS Gate") | quality gate failed |
| 4 | **Security** | Bandit (SAST), pip-audit (dependencies), Trivy (image CVEs, CycloneDX SBOM, secrets, misconfig), in parallel | HIGH Bandit issue, vulnerable dependency, fixable CRITICAL CVE, secret/misconfig |
| 5 | **Deploy** | Docker Compose deploy to **staging**, health + version check, **automatic rollback**, Selenium browser tests | unhealthy deploy, failing e2e test |
| 6 | **Release** | Full dataset downloaded and SHA-256 verified, **same image** promoted to **production**, e2e tests, Git tag and GitHub Release with SBOM | any failure (production rolled back) |
| 7 | **Monitoring** | Prometheus/Alertmanager/Grafana stack updated and verified, release annotation, optional incident simulation | monitoring not healthy, alert not firing |

- **Trigger:** Jenkins polls GitHub every two minutes (a local Jenkins cannot receive webhooks), so every commit starts a build.
- **Safety:** concurrent builds are disabled, secrets are Jenkins credentials injected with `withCredentials` and masked in logs.
- **Notifications:** Jenkins e-mails `SUCCESS` / `FAILED` (with the log attached) after every build; Alertmanager e-mails `FIRING` / `RESOLVED` for production alerts.

Full details: **[docs/PIPELINE.md](docs/PIPELINE.md)** · Security controls and findings: **[SECURITY.md](SECURITY.md)**.

### 🌍 Environments

| | Staging | Production |
|---|---|---|
| URL | http://localhost:8502 | http://localhost:8501 |
| Data | ~2 % sample baked into the image | full dataset (3.3 M transactions), read-only volume |
| Limits | 1 GB RAM, 1 CPU | 6 GB RAM, 2 CPUs |
| Browser tests | ≥ 1,000 rows | ≥ 100,000 rows (proves the full dataset is served) |
| Config | `deploy/staging.env` | `deploy/production.env` |

One Compose file (`deploy/docker-compose.app.yml`) serves both environments; the differences live in the `.env` files (environment-specific configuration as code). Deployment history is kept in `/var/jenkins_home/deploy-state/history.log`.

### 🏷️ Versioning

- **Application:** the `VERSION` file holds `major.minor` (changed by the developer); Jenkins appends the build number, e.g. `1.0` + build `24` → **`1.0.24`**. The same number appears on the Docker image, the sidebar, the `cs_app_info` metric, SonarQube, the Git tag `v1.0.24`, the GitHub Release, the Grafana annotation and the notification e-mail.
- **Data:** versioned separately as the GitHub Release `dataset-v1` (see [Dataset](#-dataset)).
- **Images:** every version stays in the registry (`http://localhost:5000/v2/cs-app/tags/list`); `stable` points to the last release that passed production.

### 📦 Project Structure

```
Customer-Segmentation-Analysis/
├── Jenkinsfile                  # 7-stage declarative pipeline (Pipeline as Code)
├── Dockerfile                   # App image: Python 3.12 slim, non-root, healthcheck
├── VERSION                      # Major.minor version; Jenkins appends the build number
├── sonar-project.properties     # SonarQube analysis settings
├── SECURITY.md                  # Security controls, gating policy, findings register
├── requirements-dev.txt         # CI tooling (pytest, flake8, bandit, pip-audit, selenium)
│
├── src/
│   ├── app.py                   # Streamlit entry point & page navigation
│   ├── serve.py                 # Container entry point: metrics exporter + Streamlit
│   ├── telemetry.py             # Prometheus metrics for the app
│   ├── requirements.txt         # Direct runtime dependencies (pinned)
│   ├── requirements.lock        # Fully resolved, hash-verified lock file
│   ├── data/                    # Small CSVs, sample/ dataset, dataset.sha256
│   ├── model/
│   │   ├── AttitudeAnalysis.py      # Main entry point: load → clean → merge → EDA → segment → visualise
│   │   ├── DataLoader.py            # Reads the 5 raw CSV files (supports DATA_DIR)
│   │   ├── TableCleaner.py          # Cleans each raw table individually
│   │   ├── Merger.py                # Merges cleaned tables into one master table
│   │   ├── EDA.py                   # Answers the project's guiding analysis questions
│   │   ├── CustomerSegmentation.py  # Builds RFM scores and assigns segments
│   │   └── Visualizer.py            # Generates and saves all charts
│   └── views/
│       ├── Dashboard.py         # EDA tables: missing values, spending, trends, segment profile
│       ├── Analytics.py         # Chart gallery: all Visualizer outputs
│       └── Recommendation.py    # Business recommendations per segment
│
├── tests/                       # unit/, integration/, e2e/ (Selenium), synthetic data factory
├── scripts/                     # make_sample.py, package_dataset.py (large-data tooling)
├── ci/                          # One script per pipeline stage (runnable locally too)
├── deploy/                      # Compose file + staging.env / production.env
├── infra/                       # Jenkins, SonarQube, registry (docker compose)
├── monitoring/                  # Prometheus, Alertmanager, Grafana, alert rules + tests
└── docs/PIPELINE.md             # Pipeline documentation and runbook
```

---

## 📊 Dataset

A public, synthetic financial dataset (Kaggle) covering customer transactions, cards and user profiles from banking institutions over **2010–2019**, made up of 5 tables:

| Table | Description |
|---|---|
| **Transaction Data** | Every transaction: amount, date, channel (Swipe/Chip/Online), merchant, errors |
| **Card Data** | Card brand/type, credit limit, chip status, dark-web exposure flag |
| **Merchant Category (MCC) Data** | Merchant category codes and descriptions |
| **Fraud Labels Data** | Whether a transaction was flagged as fraudulent |
| **User Data** | Age, income, debt, credit score and other demographics |

### 📁 Handling the large files

`transactions_data_25pc.csv` (~300 MB) and `train_fraud_labels.csv` (~110 MB) exceed GitHub's 100 MB file limit, so **data is versioned separately from code**:

| Where | What | Used by |
|---|---|---|
| `src/data/*.csv` (Git) | cards, users and MCC tables (small) | everything |
| `src/data/sample/` (Git) | ~2 % random sample of transactions + matching fraud labels, card numbers/CVVs removed | tests, container smoke test, staging |
| `src/data/dataset.sha256` (Git) | SHA-256 checksums of the `.gz` archives and of the unpacked CSVs | integrity check |
| **GitHub Release [`dataset-v1`](../../releases/tag/dataset-v1)** | `transactions_data_25pc.csv.gz`, `train_fraud_labels.csv.gz` | production (downloaded once, verified and cached by Jenkins) |

**Publishing a new dataset version**

```bash
python scripts/make_sample.py          # regenerate the committed sample
python scripts/package_dataset.py      # dist/dataset/*.csv.gz + src/data/dataset.sha256
git add src/data/dataset.sha256 && git commit -m "Dataset v2 checksums" && git push
gh release create dataset-v2 dist/dataset/*.gz --title "Dataset v2"
```

Then update `DATASET_TAG` in the `Jenkinsfile` and `DATA_DIR` in `deploy/production.env`.

---

## 🔄 Data Pipeline

1. **Load**: `DataLoader` reads all 5 CSVs (from `src/data/` or the folder given by `DATA_DIR`) with pandas' multi-threaded pyarrow engine.
2. **Clean**: `TableCleaner` handles each table individually: strips currency symbols, imputes missing values (median for numeric, mode for categorical), converts ID columns to clean strings, parses dates, derives flags like `is_error` and `is_fraud`, and drops card numbers and CVVs (never used by the analysis).
3. **Merge**: `Merger` joins all tables into one transaction-level master table (`card_id`, `client_id` and `mcc` as join keys).
4. **Analyse**: `EDA` computes missing-value reports, spending overviews, channel and card-type breakdowns, yearly trends and top merchant categories.
5. **Segment**: `CustomerSegmentation` builds an RFM table per customer and scores it into 5 segments.
6. **Visualise**: `Visualizer` renders and saves the 9 charts used across the dashboard (the density curve of the amount histogram is fitted on a fixed 200,000-row sample to keep chart generation fast on the full dataset).

---

## 🧮 RFM Segmentation Methodology

| Metric | Definition |
|---|---|
| **Recency** | Days since a customer's most recent transaction |
| **Frequency** | Total number of transactions per customer |
| **Monetary** | Total amount spent by the customer |

Each metric is scored 1–4 using quantiles, summed into an `RFM_score`, and mapped to a segment:

| RFM Score | Segment | Customers (full dataset) |
|---|---|---|
| 10–12 | Champions | 189 |
| 8–9 | Loyal Customers | 320 |
| 6–7 | Potential Loyalists | 333 |
| 4–5 | At Risk | 304 |
| 0–3 | Lost | 73 |

---

## 💡 Key Recommendations

- **Champions**: small but highest-spending group → VIP/loyalty programmes and personalised offers.
- **Potential Loyalists**: largest group, lower spending → upselling, cross-selling, increase transaction frequency.
- **At Risk**: declining spend → win-back campaigns with discounts or cashback.
- **Lost**: low spend → low-cost reactivation only; stop investing if unresponsive.
- Grocery, Food Stores and Service Stations are the top merchant categories → cashback/rewards partnerships through these merchants.
- Online transactions have the highest-value outliers → strengthen online fraud detection.
- Transaction value grew steadily until ~2015 then plateaued → prioritise new customer acquisition and product expansion.

---

## ▶️ How to Run

### Option 1: Locally (Python 3.12)

```bash
python -m venv .venv                     # Windows with several Pythons: py -3.12 -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install --require-hashes -r src/requirements.lock
pip install -r requirements-dev.txt      # only needed for tests and linters

cd src
streamlit run app.py                     # open http://localhost:8501
```

- **Python 3.12 is required**: the lock file is resolved for the same Python version as the Docker image.
- **Full dataset:** download the two `.gz` files from the [`dataset-v1` release](../../releases/tag/dataset-v1) and unzip them into `src/data/`.
- **Quick start without downloading:** run on the committed sample instead:
  - Windows PowerShell: `$env:DATA_DIR="data/sample"; streamlit run app.py`
  - macOS/Linux: `DATA_DIR=data/sample streamlit run app.py`

### Option 2: Docker

```bash
docker build -t cs-app .
docker run --rm -p 8501:8501 cs-app      # serves the sample dataset baked into the image
```

### Option 3: The full DevOps platform

```bash
git clone https://github.com/MinhMan1301/Customer-Segmentation-Analysis.git
cd Customer-Segmentation-Analysis
docker compose -f infra/docker-compose.yml up -d --build
```

This starts Jenkins, SonarQube and a local Docker registry, and creates the shared `devops-net` network and `cs-datasets` volume. Configure the four Jenkins credentials (`github-creds`, `sonarqube-token`, `smtp-creds`, `grafana-admin`) and the Pipeline job as described in [docs/PIPELINE.md](docs/PIPELINE.md#6-one-time-setup-summary). From then on, every push runs the whole pipeline, which also brings up staging, production and the monitoring stack.

| Service | URL |
|---|---|
| Production app | http://localhost:8501 |
| Staging app | http://localhost:8502 |
| Jenkins | http://localhost:8080 |
| SonarQube | http://localhost:9000 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |
| Docker registry | http://localhost:5000/v2/_catalog |

> ⚠️ Do not start, stop or replace the staging/production containers by hand while a build is running: the pipeline verifies the running version and will fail and roll back if the container changes underneath it.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATA_DIR` | `src/data` | Folder containing the 5 CSV files |
| `CHART_DIR` | `charts` | Where generated charts are written |
| `METRICS_ENABLED` | `true` | Turn the Prometheus exporter on/off |
| `METRICS_PORT` / `METRICS_ADDR` | `8000` / `127.0.0.1` | Exporter port and bind address (`0.0.0.0` inside Docker) |
| `APP_VERSION`, `APP_ENV` | `dev`, `local` | Shown in the sidebar and in the `cs_app_info` metric |

Jenkins build parameters: `RELEASE_TO_PRODUCTION` (default on) and `SIMULATE_INCIDENT` (default off).

---

## 🧪 Testing

```bash
python -m pytest -m "not e2e"                        # unit + integration tests (96.8 % coverage)
python -m pytest -m "not e2e" --cov --cov-report=term
flake8 src tests scripts                             # style + complexity
bandit -r src scripts                                # security linting
```

- **Unit tests**: cleaning rules, merge logic, EDA, RFM scoring thresholds, data loader, charts, telemetry, dataset scripts.
- **Integration tests**: the full load → clean → merge → segment pipeline, a data contract for the committed sample, and every Streamlit page rendered headlessly with `AppTest`.
- **Smoke test**: the freshly built image is started once to check its health endpoint, its reported version and that the pipeline produces all 9 charts.
- **End-to-end tests**: Selenium opens the deployed app in Chromium, checks every page, the deployed version and the dataset size, and saves screenshots (run by Jenkins after each deployment).

Unit tests use a seeded synthetic dataset (`tests/data_factory.py`), so they never depend on the large files.

---

## 🛡️ Code Quality & Security

- **SonarQube "CS Gate"** fails the build if coverage is below 80 %, duplication is above 3 %, or any maintainability, reliability or security rating is worse than A. Data files and generated charts are excluded from analysis. Latest analysis: 669 lines of Python, 0 bugs, 0 vulnerabilities, 0.0 % duplication, 96.4 % coverage.
- **Security gates:** HIGH Bandit issues, any vulnerable dependency, fixable CRITICAL image CVEs, and any HIGH/CRITICAL secret or misconfiguration stop the pipeline. All findings, their severity and how they were handled are recorded in **[SECURITY.md](SECURITY.md)**.
- **Hardening:** non-root containers with all capabilities dropped, ports bound to `127.0.0.1`, hash-verified dependencies, pinned and checksummed tooling, SHA-256-verified production data.

---

## 📈 Monitoring & Alerting

The app exposes Prometheus metrics on an internal port (`/metrics`), including the running version, rows loaded, fraud rate, customers per segment, page views/errors, page render time, and memory/CPU usage relative to the container limits. Grafana shows them on a provisioned dashboard with a marker for every Jenkins release.

| Alert | Severity | Fires when |
|---|---|---|
| `CSAppDown` | critical | health check fails for 30 s |
| `CSDataPipelineFailed` | critical | loading/cleaning/segmenting the data raised an error |
| `CSMetricsTargetDown` | warning | metrics endpoint unreachable for 1 min |
| `CSHighMemoryUsage` | warning | memory > 85 % of the container limit |
| `CSHighCPU` | warning | CPU > 90 % of the container limit for 5 min |
| `CSSlowHealthCheck` | warning | health check slower than 2 s |
| `CSPageErrors` | warning | a dashboard page raised an exception |

Alerts are e-mailed by Alertmanager when they fire and when they resolve, and every alert rule is unit-tested with `promtool`.

### 🚨 Incident drill

In Jenkins, choose **Build with Parameters** and tick **`SIMULATE_INCIDENT`**. After the release, the pipeline stops production on purpose, waits for `CSAppDown` to fire, restarts the app, waits for the alert to resolve and writes `reports/monitoring/incident.json` with the measured times. In the last drill the alert fired after **55 s** and production recovered after **83 s**. The drill is off by default so that normal releases cause no downtime.

---

## 🔮 Future Work

- **Fraud prediction**: train a classification model on the existing fraud labels to flag suspicious transactions.
- **Churn prediction**: predict which customers are likely to move into the *At Risk* segment so Company X can act early.
- **MLOps pipeline**: add model training and evaluation stages with quality thresholds, versioned models in a model registry, and model-performance / data-drift monitoring in Grafana.
- **Data versioning with DVC**: replace GitHub Release assets with DVC backed by cloud storage (e.g. Amazon S3).
- **Webhook trigger**: expose Jenkins through a tunnel or host it in the cloud so GitHub can trigger builds instantly instead of polling.

---

## 🎥 Video Demo

[**Video Demo: Customer Transaction Analysis & Segmentation — DevOps Pipeline with Jenkins**](ADD_VIDEO_LINK_HERE)

---

## 📬 Contact

**Author:** Pham Nguyen Minh Man ([MinhMan1301](https://github.com/MinhMan1301))
📧 Email: [phamminhman1312005@gmail.com](mailto:phamminhman1312005@gmail.com)
🔗 GitHub: [MinhMan1301](https://github.com/MinhMan1301)
🔗 LinkedIn: [NGUYEN MINH MAN PHAM](https://www.linkedin.com/in/nguyen-minh-man-pham-47b493311/)
