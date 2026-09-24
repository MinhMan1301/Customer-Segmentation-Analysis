#!/usr/bin/env bash
# RELEASE: after production is verified, mark the image as stable, tag the commit
# and publish a GitHub Release with the build metadata and SBOM attached.
source "$(dirname "$0")/lib.sh"
require_env REGISTRY APP_NAME APP_VERSION GIT_SHA GITHUB_REPO GH_USER GH_TOKEN

tag="v${APP_VERSION}"
image="$(image_ref)"
remote="https://${GH_USER}:${GH_TOKEN}@github.com/${GITHUB_REPO}.git"
api="https://api.github.com/repos/${GITHUB_REPO}"
gh_api() { curl -fsS -H "Authorization: Bearer ${GH_TOKEN}" -H "Accept: application/vnd.github+json" "$@"; }

log "Promoting $image to ${REGISTRY}/${APP_NAME}:stable"
docker tag "$image" "${REGISTRY}/${APP_NAME}:stable"
docker push "${REGISTRY}/${APP_NAME}:stable"

log "Creating git tag $tag on $GIT_SHA"
if git ls-remote --exit-code --tags "$remote" "refs/tags/$tag" >/dev/null 2>&1; then
  die "tag $tag already exists on GitHub - bump the VERSION file"
fi
git tag -d "$tag" >/dev/null 2>&1 || true
git -c user.name="Jenkins CI" -c user.email="jenkins@localhost" \
  tag -a "$tag" "$GIT_SHA" -m "Release $tag (Jenkins build ${BUILD_NUMBER:-local})"
git push "$remote" "refs/tags/$tag"

log "Publishing GitHub Release $tag"
digest="$(jq -r .digest "$REPORTS_DIR/build-info.json" 2>/dev/null || echo unknown)"
body="$(cat <<MD
Automated release from Jenkins build [#${BUILD_NUMBER:-local}](${BUILD_URL:-}).

| Item | Value |
|---|---|
| Image | \`${image}\` (also \`:stable\`) |
| Digest | \`${digest}\` |
| Commit | \`${GIT_SHA}\` |
| Verified in | staging (Selenium) -> production (health, version, Selenium) |
| Production data | GitHub Release \`${DATASET_TAG:-dataset-v1}\` (SHA-256 verified) |

Attached: \`build-info.json\`, CycloneDX SBOM \`sbom.cdx.json\`.
MD
)"
payload="$(jq -n --arg tag "$tag" --arg sha "$GIT_SHA" --arg body "$body" \
  '{tag_name: $tag, target_commitish: $sha, name: ("Release " + $tag), body: $body,
    generate_release_notes: true, make_latest: "true"}')"
release="$(gh_api -X POST "$api/releases" -d "$payload")"
upload_url="$(jq -r '.upload_url | sub("\\{.*\\}$"; "")' <<<"$release")"

for asset in "$REPORTS_DIR/build-info.json" "$REPORTS_DIR/security/sbom.cdx.json"; do
  [[ -f "$asset" ]] || continue
  gh_api -X POST -H "Content-Type: application/json" --data-binary "@$asset" \
    "${upload_url}?name=$(basename "$asset")" >/dev/null
  echo "Attached $(basename "$asset")"
done

jq -r '"Release published: \(.html_url)"' <<<"$release" | tee "$REPORTS_DIR/release.txt"
