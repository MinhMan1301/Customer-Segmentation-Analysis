#!/usr/bin/env bash
# Selenium browser tests against a deployed environment (staging in Deploy, production in Release).
# Usage: bash ci/e2e.sh staging|production
source "$(dirname "$0")/lib.sh"
env_name="${1:-}"
[[ "$env_name" =~ ^(staging|production)$ ]] || die "usage: $0 staging|production"
activate_python_env
# shellcheck disable=SC1090
source "deploy/${env_name}.env"   # E2E_MIN_DATASET_ROWS, E2E_TIMEOUT

SELENIUM_IMAGE="${SELENIUM_IMAGE:-selenium/standalone-chromium:4.49.0-20260909}"
selenium="cs-selenium-${BUILD_NUMBER:-local}"
cleanup() { docker rm -f "$selenium" >/dev/null 2>&1 || true; }
trap cleanup EXIT
cleanup

log "Starting Selenium ($SELENIUM_IMAGE)"
docker run -d --name "$selenium" --network devops-net --shm-size=2g "$SELENIUM_IMAGE" >/dev/null
wait_for_http "http://${selenium}:4444/status" 120

log "Browser tests against $env_name"
E2E_APP_URL="http://cs-${env_name}-app:8501" \
E2E_SELENIUM_URL="http://${selenium}:4444/wd/hub" \
E2E_TIMEOUT="${E2E_TIMEOUT:-180}" \
E2E_EXPECTED_VERSION="${APP_VERSION:-}" \
E2E_METRICS_URL="http://cs-${env_name}-app:8000/metrics" \
E2E_MIN_DATASET_ROWS="${E2E_MIN_DATASET_ROWS:-1}" \
E2E_ARTIFACT_DIR="$REPORTS_DIR/e2e/$env_name" \
  python -m pytest tests/e2e -m e2e -p no:cacheprovider \
    --junitxml="$REPORTS_DIR/e2e-${env_name}.xml" -o junit_suite_name="e2e-${env_name}"
