#!/usr/bin/env bash
# TEST (part 1): unit + integration tests with coverage gate (e2e runs after deployment).
source "$(dirname "$0")/lib.sh"
setup_python_env
activate_python_env
mkdir -p "$REPORTS_DIR"

log "pytest: unit + integration (coverage gate 80%)"
REQUIRE_SAMPLE_DATA=1 python -m pytest -m "not e2e" \
  --junitxml="$REPORTS_DIR/junit.xml" \
  --cov --cov-report=term --cov-report="xml:$REPORTS_DIR/coverage.xml" \
  --cov-report="html:$REPORTS_DIR/coverage-html" \
  --cov-fail-under=80
