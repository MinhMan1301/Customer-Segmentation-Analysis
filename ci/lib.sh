#!/usr/bin/env bash
# Shared helpers for the ci/*.sh scripts. Source it, do not execute it.
set -euo pipefail
umask 022

log() { printf '\n==> [%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

require_env() {
  local name
  for name in "$@"; do
    [[ -n "${!name:-}" ]] || die "environment variable $name is required"
  done
}

REPORTS_DIR="${REPORTS_DIR:-reports}"
VENV_DIR="${VENV_DIR:-.venv}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
# Caches live in jenkins_home so they survive container restarts.
CI_HOME="${JENKINS_HOME:-${HOME:-/tmp}}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$CI_HOME/.cache/uv}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$CI_HOME/.local/share/uv/python}"
export TRIVY_CACHE_DIR="${TRIVY_CACHE_DIR:-$CI_HOME/.cache/trivy}"

# <owner>/<repo>: taken from the Jenkinsfile, or derived from the URL Jenkins cloned.
if [[ -z "${GITHUB_REPO:-}" || "${GITHUB_REPO}" == CHANGE_ME* ]]; then
  GITHUB_REPO="$(sed -E 's#^(https://([^@/]+@)?github\.com/|git@github\.com:)##; s#\.git$##' <<<"${GIT_URL:-}")"
  export GITHUB_REPO
fi

# Create (once) and update the workspace virtualenv with uv - much faster than pip.
setup_python_env() {
  command -v uv >/dev/null || die "uv is not installed on this Jenkins agent"
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    log "Creating Python $PYTHON_VERSION virtualenv in $VENV_DIR"
    uv venv --python "$PYTHON_VERSION" "$VENV_DIR"
  fi
  log "Installing the hash-locked runtime dependencies + CI tooling"
  uv pip install --quiet --python "$VENV_DIR/bin/python" -r src/requirements.lock -r requirements-dev.txt
}

activate_python_env() {
  [[ -x "$VENV_DIR/bin/python" ]] || setup_python_env
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
}

# wait_for_http URL [TIMEOUT_SECONDS]
wait_for_http() {
  local url="$1" timeout="${2:-120}" waited=0
  until curl -fsS -o /dev/null --max-time 5 "$url"; do
    (( waited >= timeout )) && { echo "Timed out after ${timeout}s waiting for $url" >&2; return 1; }
    sleep 3
    waited=$(( waited + 3 ))
  done
  echo "OK: $url (after ${waited}s)"
}

# check_metrics_version METRICS_URL EXPECTED_VERSION
check_metrics_version() {
  local url="$1" expected="$2" metrics
  metrics="$(curl -fsS --max-time 10 "$url")" || { echo "Cannot read $url" >&2; return 1; }
  if ! grep -q "^cs_app_info{.*version=\"${expected}\"" <<<"$metrics"; then
    echo "Expected version $expected in $url, found:" >&2
    grep '^cs_app_info' <<<"$metrics" >&2 || true
    return 1
  fi
  echo "OK: $url reports version $expected"
}

image_ref() { echo "${REGISTRY}/${APP_NAME}:${APP_VERSION}"; }
