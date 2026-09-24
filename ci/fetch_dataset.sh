#!/usr/bin/env bash
# Download the FULL dataset (too big for Git) from the GitHub Release $DATASET_TAG,
# verify it against the committed checksums and unpack it into the shared volume
# that the production container mounts read-only. Cached: runs once per dataset version.
source "$(dirname "$0")/lib.sh"
require_env GITHUB_REPO DATASET_TAG
for cmd in curl jq sha256sum gunzip; do command -v "$cmd" >/dev/null || die "$cmd is required"; done

DATASET_ROOT="${DATASET_ROOT:-/datasets}"
GITHUB_API="${GITHUB_API:-https://api.github.com}"
manifest="$PWD/src/data/dataset.sha256"
target="$DATASET_ROOT/$DATASET_TAG"
[[ -f "$manifest" ]] || die "missing $manifest - run scripts/package_dataset.py and commit it"

if [[ -f "$target/.complete" ]] && cmp -s "$manifest" "$target/.complete"; then
  log "Dataset $DATASET_TAG already present and verified in $target (cache hit)"
else
  mkdir -p "$DATASET_ROOT"
  work="$(mktemp -d "$DATASET_ROOT/.download-XXXXXX")"
  trap 'rm -rf "$work"' EXIT
  auth=()
  if [[ -n "${GH_TOKEN:-}" ]]; then auth=(-H "Authorization: Bearer ${GH_TOKEN}"); fi
  api="$GITHUB_API/repos/${GITHUB_REPO}"

  log "Reading release $DATASET_TAG of $GITHUB_REPO"
  curl -fsSL "${auth[@]}" -H "Accept: application/vnd.github+json" \
    "$api/releases/tags/$DATASET_TAG" -o "$work/release.json"

  grep '\.gz$' "$manifest" > "$work/archives.sha256"
  grep -v '\.gz$' "$manifest" > "$work/files.sha256" || true
  while read -r _checksum name; do
    asset_id="$(jq -r --arg n "$name" '.assets[] | select(.name == $n) | .id' "$work/release.json")"
    [[ -n "$asset_id" && "$asset_id" != "null" ]] || die "asset $name not found in release $DATASET_TAG"
    log "Downloading $name (asset $asset_id)"
    curl -fL --retry 3 --progress-bar "${auth[@]}" -H "Accept: application/octet-stream" \
      "$api/releases/assets/$asset_id" -o "$work/$name"
  done < "$work/archives.sha256"

  log "Verifying SHA-256 of the downloaded archives"
  (cd "$work" && sha256sum -c archives.sha256)

  mkdir -p "$work/$DATASET_TAG"
  while read -r _checksum name; do
    gunzip -c "$work/$name" > "$work/$DATASET_TAG/${name%.gz}"
  done < "$work/archives.sha256"
  if [[ -s "$work/files.sha256" ]]; then
    log "Verifying SHA-256 of the unpacked CSV files"
    (cd "$work/$DATASET_TAG" && sha256sum -c "$work/files.sha256")
  fi
  cp src/data/cards_data.csv src/data/users_data.csv src/data/mcc_codes.csv "$work/$DATASET_TAG/"
  cp "$manifest" "$work/$DATASET_TAG/.complete"
  chmod 0755 "$work/$DATASET_TAG"            # mktemp dirs are 0700; the app runs as uid 10001
  chmod -R a+rX "$work/$DATASET_TAG"

  rm -rf "$target"
  mv "$work/$DATASET_TAG" "$target"
fi

log "Production dataset:"
ls -lh "$target"
