#!/usr/bin/env bash
# MONITORING & ALERTING: Prometheus + Alertmanager (email) + Blackbox exporter + Grafana.
# Usage: bash ci/monitoring.sh up|verify|incident
source "$(dirname "$0")/lib.sh"
MON_DIR="$REPORTS_DIR/monitoring"
mkdir -p "$MON_DIR"
PROM="http://cs-prometheus:9090"
AM="http://cs-alertmanager:9093"
GRAFANA="http://cs-grafana:3000"
PROD_APP="cs-production-app"

prom_query() {  # prints the JSON result of an instant query
  curl -fsS --get --data-urlencode "query=$1" "$PROM/api/v1/query"
}

monitored_envs() {  # environments that currently have a running app container
  local env_name
  for env_name in production staging; do
    if [[ "$(docker inspect -f '{{.State.Running}}' "cs-${env_name}-app" 2>/dev/null)" == "true" ]]; then
      echo "$env_name"
    fi
  done
}

do_up() {
  require_env SMTP_USER SMTP_PASSWORD ALERT_EMAIL_TO GRAFANA_USER GRAFANA_PASSWORD
  log "Starting / updating the monitoring stack (configs are baked into the images)"
  docker compose -p cs-monitoring -f monitoring/docker-compose.yml up -d --build --wait --wait-timeout 180
  docker compose -p cs-monitoring -f monitoring/docker-compose.yml ps
  # Pick up changed rules without a restart (lifecycle API is enabled).
  curl -fsS -X POST "$PROM/-/reload" && echo "Prometheus configuration reloaded"
}

do_verify() {
  require_env GRAFANA_USER GRAFANA_PASSWORD
  wait_for_http "$PROM/-/ready" 60
  wait_for_http "$AM/-/ready" 60
  wait_for_http "$GRAFANA/api/health" 90

  log "Validating the monitoring configuration inside the running containers"
  docker exec cs-prometheus promtool check config /etc/prometheus/prometheus.yml
  docker exec -w /etc/prometheus cs-prometheus promtool test rules alert_rules_test.yml | tee "$MON_DIR/rule-tests.txt"
  docker exec cs-alertmanager amtool check-config /tmp/alertmanager.yml | grep -v -i password

  local env_name value waited
  for env_name in $(monitored_envs); do
    log "Waiting until Prometheus scrapes $env_name"
    waited=0
    while :; do
      value="$(prom_query "min(up{job=\"cs-app\",env=\"$env_name\"}) * min(probe_success{env=\"$env_name\"})" \
        | jq -r '.data.result[0].value[1] // "0"')"
      [[ "$value" == "1" ]] && break
      (( waited >= 120 )) && die "Prometheus cannot scrape/probe the $env_name app"
      sleep 5; waited=$(( waited + 5 ))
    done
    echo "OK: $env_name is up and probed"
  done

  local rules
  rules="$(curl -fsS "$PROM/api/v1/rules" | tee "$MON_DIR/rules.json" | jq '[.data.groups[].rules[]] | length')"
  (( rules >= 6 )) || die "expected at least 6 alert rules, Prometheus loaded $rules"
  echo "OK: $rules alert rules loaded"

  curl -fsS "$PROM/api/v1/targets" | tee "$MON_DIR/targets.json" \
    | jq -r '.data.activeTargets[] | "\(.labels.job)\t\(.labels.env // "-")\t\(.health)\t\(.scrapeUrl)"'
  curl -fsS "$AM/api/v2/alerts" > "$MON_DIR/alerts-now.json"
  echo "Active alerts: $(jq length "$MON_DIR/alerts-now.json")"

  log "Live application metrics"
  prom_query 'cs_app_info' | jq -r '.data.result[] | "\(.metric.env): version \(.metric.version)"'
  prom_query 'cs_dataset_rows' | jq -r '.data.result[] | "\(.metric.env): \(.value[1]) rows loaded"'

  if [[ -n "${APP_VERSION:-}" ]]; then
    log "Grafana release annotation"
    jq -n --arg v "$APP_VERSION" --arg url "${BUILD_URL:-}" \
      '{tags: ["release", "jenkins", $v], text: ("Jenkins deployed v" + $v + " " + $url)}' \
    | curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" -H "Content-Type: application/json" \
        -X POST "$GRAFANA/api/annotations" --data-binary @- | tee "$MON_DIR/annotation.json"
    echo
  fi
}

do_incident() {
  local app="$PROD_APP"
  docker inspect "$app" >/dev/null 2>&1 || die "production is not running - nothing to test"
  trap 'docker start "$PROD_APP" >/dev/null 2>&1 || true' EXIT

  log "INCIDENT SIMULATION: stopping $app"
  docker stop "$app" >/dev/null
  start="$(date +%s)"

  waited=0
  until curl -fsS "$AM/api/v2/alerts?active=true&filter=alertname%3D%22CSAppDown%22&filter=env%3D%22production%22" \
        | tee "$MON_DIR/incident-alert.json" | jq -e 'length > 0' >/dev/null; do
    (( waited >= 240 )) && die "CSAppDown alert did not reach Alertmanager within 240s"
    sleep 5; waited=$(( waited + 5 ))
  done
  detected="$(date +%s)"; mttd=$(( detected - start ))
  echo "ALERT FIRING: CSAppDown reached Alertmanager after ${mttd}s -> email sent to the team"

  log "Recovering: starting $app again"
  docker start "$app" >/dev/null
  wait_for_http "http://$app:8501/_stcore/health" 120
  trap - EXIT

  waited=0
  until [[ "$(prom_query 'ALERTS{alertname="CSAppDown",env="production",alertstate="firing"}' \
              | jq '.data.result | length')" == "0" ]]; do
    (( waited >= 300 )) && die "CSAppDown did not resolve within 300s"
    sleep 5; waited=$(( waited + 5 ))
  done
  resolved="$(date +%s)"
  echo "RESOLVED after $(( resolved - start ))s total (resolved email sent)"

  jq -n --argjson mttd "$mttd" --argjson mttr "$(( resolved - start ))" \
    '{scenario: "production container stopped", alert: "CSAppDown",
      time_to_detect_seconds: $mttd, time_to_recover_seconds: $mttr}' | tee "$MON_DIR/incident.json"
}

case "${1:-}" in
  up) do_up ;;
  verify) do_verify ;;
  incident) do_incident ;;
  *) die "usage: $0 up|verify|incident" ;;
esac
