#!/usr/bin/env bash
# CODE QUALITY (local linters). SonarQube analysis + quality gate run in the Jenkinsfile.
source "$(dirname "$0")/lib.sh"
activate_python_env
mkdir -p "$REPORTS_DIR"
status=0

log "flake8 (style + cyclomatic complexity <= 10; report imported by SonarQube)"
flake8 src tests scripts --exit-zero --output-file "$REPORTS_DIR/flake8.txt" --tee
echo "flake8 findings: $(wc -l < "$REPORTS_DIR/flake8.txt")"

log "flake8 hard gate: syntax errors and undefined names"
flake8 src tests scripts --select=E9,F63,F7,F82 || status=1

mapfile -t dockerfiles < <(git ls-files '*Dockerfile')
log "hadolint $(hadolint --version | awk '{print $NF}') on ${#dockerfiles[@]} Dockerfiles (policy: .hadolint.yaml)"
hadolint --config .hadolint.yaml "${dockerfiles[@]}" | tee "$REPORTS_DIR/hadolint.txt" || status=1

mapfile -t scripts < <(git ls-files '*.sh')
log "shellcheck on ${#scripts[@]} shell scripts"
shellcheck --severity=warning --external-sources "${scripts[@]}" | tee "$REPORTS_DIR/shellcheck.txt" || status=1

exit "$status"
