#!/usr/bin/env bash
# DEPLOY / RELEASE: docker compose deployment with health verification and automatic rollback.
# Usage: bash ci/deploy.sh deploy|rollback staging|production
source "$(dirname "$0")/lib.sh"
action="${1:-}"; env_name="${2:-}"
[[ "$env_name" =~ ^(staging|production)$ ]] || die "usage: $0 deploy|rollback staging|production"

env_file="deploy/${env_name}.env"
project="cs-${env_name}"
container="cs-${env_name}-app"
state_dir="${DEPLOY_STATE_DIR:-${HOME:-/tmp}/deploy-state}"
mkdir -p "$state_dir"
current_file="$state_dir/${env_name}.current"
previous_file="$state_dir/${env_name}.previous"
history_file="$state_dir/history.log"

record() { printf '%s %-10s %-8s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$env_name" "$1" "$2" >> "$history_file"; }

compose() {
  local image="$1"; shift
  APP_IMAGE="$image" docker compose -p "$project" --env-file "$env_file" -f deploy/docker-compose.app.yml "$@"
}

start() {
  compose "$1" up -d --wait --wait-timeout 300 --remove-orphans
}

verify() {
  local expected_version="${1:-}"
  wait_for_http "http://${container}:8501/_stcore/health" 90 || return 1
  wait_for_http "http://${container}:8000/metrics" 30 || return 1
  if [[ -n "$expected_version" ]]; then
    check_metrics_version "http://${container}:8000/metrics" "$expected_version" || return 1
  fi
}

do_deploy() {
  require_env REGISTRY APP_NAME APP_VERSION
  local image previous=""
  image="$(image_ref)"
  [[ -f "$current_file" ]] && previous="$(cat "$current_file")"
  log "Deploying $image to $env_name (currently running: ${previous:-nothing})"

  if start "$image" && verify "$APP_VERSION"; then
    if [[ -n "$previous" && "$previous" != "$image" ]]; then
      echo "$previous" > "$previous_file"
    fi
    echo "$image" > "$current_file"
    record deploy "$image"
    docker ps --filter "name=^${container}$" --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
    log "$env_name is running $image"
    return 0
  fi

  echo "Deployment verification failed - container logs:" >&2
  docker logs --tail 100 "$container" >&2 || true
  if [[ -n "$previous" ]]; then
    log "AUTOMATIC ROLLBACK of $env_name to $previous"
    if start "$previous" && verify; then
      record auto-rollback "$previous (failed: $image)"
    else
      echo "Rollback verification failed as well!" >&2
    fi
  fi
  die "deployment of $image to $env_name failed"
}

# Called when a LATER step fails (e.g. e2e tests after a healthy deploy).
do_rollback() {
  local current="" target
  [[ -f "$current_file" ]] && current="$(cat "$current_file")"
  if [[ -n "${APP_VERSION:-}" && "$current" != "$(image_ref)" ]]; then
    echo "The running $env_name release ($current) is not from this build - nothing to roll back."
    return 0
  fi
  [[ -f "$previous_file" ]] || die "no previous release recorded for $env_name"
  target="$(cat "$previous_file")"
  log "ROLLBACK of $env_name from $current to $target"
  start "$target"
  verify
  echo "$target" > "$current_file"
  rm -f "$previous_file"   # one level of rollback; the next successful deploy records a new one
  record rollback "$target (from: $current)"
}

case "$action" in
  deploy) do_deploy ;;
  rollback) do_rollback ;;
  *) die "usage: $0 deploy|rollback staging|production" ;;
esac
