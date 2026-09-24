#!/usr/bin/env bash
# SECURITY: bandit (SAST) | pip-audit (dependency CVEs) | trivy (image CVEs, SBOM, secrets, IaC).
# Each tool writes a full report first, then applies a gate so the evidence exists even on failure.
# Usage: bash ci/security.sh bandit|pip-audit|trivy
source "$(dirname "$0")/lib.sh"
SEC_DIR="$REPORTS_DIR/security"
mkdir -p "$SEC_DIR"

run_bandit() {
  activate_python_env
  log "Bandit: full report (all severities)"
  bandit -r src scripts -f json -o "$SEC_DIR/bandit.json" --exit-zero
  bandit -r src scripts -f html -o "$SEC_DIR/bandit.html" --exit-zero
  bandit -r src scripts -f txt --exit-zero | tee "$SEC_DIR/bandit.txt"
  log "Bandit gate: fail on HIGH severity with at least MEDIUM confidence"
  bandit -r src scripts --severity-level high --confidence-level medium --quiet
}

run_pip_audit() {
  activate_python_env
  local ignore_args=() id
  # .pip-audit-ignore: one vulnerability ID per line + justification comment (reviewed in SECURITY.md).
  if [[ -f .pip-audit-ignore ]]; then
    while read -r id _; do
      [[ -z "$id" || "$id" == \#* ]] && continue
      ignore_args+=(--ignore-vuln "$id")
    done < .pip-audit-ignore
  fi
  log "pip-audit: every runtime package in the hash-locked src/requirements.lock"
  local status=0
  pip-audit -r src/requirements.lock --disable-pip --progress-spinner off "${ignore_args[@]}" \
    -f json -o "$SEC_DIR/pip-audit.json" || status=$?
  jq -r '.dependencies[] | select(.vulns | length > 0) | "\(.name) \(.version): \([.vulns[].id] | join(", "))"' \
    "$SEC_DIR/pip-audit.json" | tee "$SEC_DIR/pip-audit.txt" || true
  [[ $status -eq 0 ]] && echo "pip-audit: no known vulnerabilities" | tee -a "$SEC_DIR/pip-audit.txt"
  return "$status"
}

run_trivy() {
  require_env REGISTRY APP_NAME APP_VERSION
  command -v trivy >/dev/null || die "trivy is not installed on this Jenkins agent"
  local image
  image="$(image_ref)"
  log "Trivy $(trivy --version | head -1) - image scan of $image"
  trivy image --scanners vuln --format json --output "$SEC_DIR/trivy-image.json" "$image"
  trivy convert --format table --output "$SEC_DIR/trivy-image.txt" "$SEC_DIR/trivy-image.json"
  jq -r '[.Results[]?.Vulnerabilities[]?.Severity] | group_by(.) | map("\(.[0]): \(length)") | join("  ")' \
    "$SEC_DIR/trivy-image.json" | tee "$SEC_DIR/trivy-image-summary.txt"

  log "Trivy: CycloneDX SBOM"
  trivy image --skip-db-update --format cyclonedx --output "$SEC_DIR/sbom.cdx.json" "$image"

  log "Trivy: repository scan for secrets and Dockerfile misconfigurations"
  trivy fs --scanners secret,misconfig --skip-dirs .venv,reports,src/data,.git,.scannerwork \
    --format table --output "$SEC_DIR/trivy-fs.txt" .
  cat "$SEC_DIR/trivy-fs.txt"

  log "Trivy gates: no fixable CRITICAL CVE in the image, no HIGH/CRITICAL secret or misconfiguration"
  trivy image --skip-db-update --scanners vuln --severity CRITICAL --ignore-unfixed \
    --ignorefile .trivyignore.yaml --exit-code 1 --format table "$image"
  trivy fs --scanners secret,misconfig --skip-dirs .venv,reports,src/data,.git,.scannerwork \
    --severity HIGH,CRITICAL --exit-code 1 --format table .
}

case "${1:-}" in
  bandit) run_bandit ;;
  pip-audit) run_pip_audit ;;
  trivy) run_trivy ;;
  *) die "usage: $0 bandit|pip-audit|trivy" ;;
esac
