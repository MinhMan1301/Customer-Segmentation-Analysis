#!/usr/bin/env bash
# TEST (part 2): start the freshly built image once and check it really works.
source "$(dirname "$0")/lib.sh"
require_env REGISTRY APP_NAME APP_VERSION

name="cs-ci-smoke-${BUILD_NUMBER:-local}"
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
cleanup

log "Starting $name from $(image_ref)"
docker run -d --name "$name" --network devops-net -e APP_ENV=ci "$(image_ref)" >/dev/null

if ! wait_for_http "http://$name:8501/_stcore/health" 90; then
  docker logs --tail 80 "$name"
  die "container did not become healthy"
fi
check_metrics_version "http://$name:8000/metrics" "$APP_VERSION"

log "Running the data pipeline inside the container on the baked-in sample data"
charts="$(docker exec "$name" python -c \
  'from model.AttitudeAnalysis import AttitudeAnalysis as A; a = A(); a.run(); print(len(a.generate_charts()))' | tail -1)"
[[ "$charts" == "9" ]] || die "expected 9 charts, got '$charts'"
echo "OK: pipeline produced $charts charts inside the image"
