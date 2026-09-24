#!/usr/bin/env bash
# BUILD: build the versioned Docker image, push it to the registry, record its digest.
source "$(dirname "$0")/lib.sh"
require_env REGISTRY APP_NAME APP_VERSION GIT_SHA

image="${REGISTRY}/${APP_NAME}"
short_sha="${GIT_SHA:0:7}"
build_date="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$REPORTS_DIR"

log "Building $image:$APP_VERSION (commit $short_sha)"
docker build --pull \
  --build-arg APP_VERSION="$APP_VERSION" \
  --build-arg GIT_SHA="$GIT_SHA" \
  --build-arg BUILD_DATE="$build_date" \
  --label "org.opencontainers.image.source=https://github.com/${GITHUB_REPO:-unknown}" \
  --label "jenkins.build.url=${BUILD_URL:-local}" \
  --tag "$image:$APP_VERSION" \
  --tag "$image:sha-$short_sha" \
  .

log "Pushing to $REGISTRY"
docker push "$image:$APP_VERSION"
docker push "$image:sha-$short_sha"

digest="$(docker inspect --format '{{index .RepoDigests 0}}' "$image:$APP_VERSION")"
size_mb="$(docker image inspect --format '{{.Size}}' "$image:$APP_VERSION" | awk '{printf "%.0f", $1/1024/1024}')"

jq -n \
  --arg image "$image" --arg version "$APP_VERSION" --arg git_sha "$GIT_SHA" \
  --arg digest "$digest" --arg built "$build_date" --arg size_mb "$size_mb" \
  --arg build_url "${BUILD_URL:-local}" --arg tags "$APP_VERSION,sha-$short_sha" \
  '{image: $image, version: $version, git_sha: $git_sha, digest: $digest, built_at: $built,
    size_mb: ($size_mb | tonumber), tags: ($tags | split(",")), jenkins_build: $build_url}' \
  > "$REPORTS_DIR/build-info.json"

cat "$REPORTS_DIR/build-info.json"
