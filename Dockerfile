# Customer Segmentation Analysis - Streamlit app image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first so this layer is cached while only the code changes.
# The lock file pins every transitive package with SHA-256 hashes (supply-chain integrity).
COPY src/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --no-create-home --shell /usr/sbin/nologin app

COPY --chown=app:app src/ ./
RUN mkdir -p /app/charts /tmp/matplotlib && chown app:app /app /app/charts /tmp/matplotlib

ARG APP_VERSION=dev
ARG GIT_SHA=unknown
ARG BUILD_DATE=unknown
LABEL org.opencontainers.image.title="customer-segmentation-analysis" \
      org.opencontainers.image.description="Streamlit dashboard for credit-card customer segmentation (RFM)" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_SHA}" \
      org.opencontainers.image.created="${BUILD_DATE}"

ENV APP_VERSION=${APP_VERSION} \
    GIT_SHA=${GIT_SHA} \
    APP_ENV=container \
    DATA_DIR=/app/data/sample \
    CHART_DIR=/app/charts \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib \
    METRICS_PORT=8000 \
    METRICS_ADDR=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

USER 10001:10001
EXPOSE 8501 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4)"]

CMD ["python", "serve.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.fileWatcherType=none"]
