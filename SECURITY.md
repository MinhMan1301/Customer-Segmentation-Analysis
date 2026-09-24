# Security

This document describes the security controls of the Customer Segmentation Analysis
pipeline, the gating policy used by the Jenkins **Security** stage, and the register of
findings and accepted risks. It is updated whenever a scanner reports something new.

## 1. Controls in the pipeline

| Layer | Tool | What it checks | Report (Jenkins artefact) | Gate (fails the build) |
|---|---|---|---|---|
| Source code (SAST) | Bandit 1.9.4 | Insecure Python patterns (eval, shell injection, weak crypto, bind-all, ...) | `reports/security/bandit.{json,html,txt}` | any **HIGH** severity issue with at least MEDIUM confidence |
| Dependencies (SCA) | pip-audit 2.10.1 | Known CVEs/GHSAs in every package of the hash-locked `src/requirements.lock` (PyPI advisory data) | `reports/security/pip-audit.{json,txt}` | **any** known vulnerability not listed in `.pip-audit-ignore` |
| Container image | Trivy 0.74.0 | OS packages + Python packages inside `cs-app:<version>` | `reports/security/trivy-image.{json,txt}` | any **CRITICAL** CVE that has a fix (`--ignore-unfixed`), minus `.trivyignore.yaml` |
| Supply chain | Trivy (CycloneDX) | Software Bill of Materials of the released image | `reports/security/sbom.cdx.json` (also attached to the GitHub Release) | - |
| Repository | Trivy fs | Hard-coded secrets, Dockerfile misconfigurations | `reports/security/trivy-fs.txt` | any **HIGH/CRITICAL** secret or misconfiguration |

Code quality (flake8, hadolint, SonarQube) runs in its own stage and is about maintainability,
not security.

Why these thresholds: the gates must stop real risk without blocking every build on noise.
Base images regularly contain LOW/MEDIUM CVEs without a fix; those are reported and reviewed,
while fixable CRITICAL issues and every vulnerable Python dependency stop the release.

## 2. Hardening built into the application and deployment

- **Data minimisation (PCI DSS):** `cards_data.csv` contains `card_number` and `cvv`, which the
  analysis never uses. `TableCleaner.clean_cards` drops both columns before any merge, so they never
  reach the dashboard, charts, logs or metrics. The committed sample dataset is generated without them
  (`scripts/make_sample.py`). Unit tests (`test_clean_cards_removes_card_number_and_cvv`,
  `test_sample_contains_no_card_secrets`, `test_full_pipeline_on_synthetic_data`) protect this behaviour.
- **Non-root container:** the app image runs as UID 10001, no shell login, `no-new-privileges`,
  all Linux capabilities dropped, memory/CPU limits per environment.
- **Least exposure:** every published port is bound to `127.0.0.1`; the metrics port 8000 is only
  reachable on the internal `devops-net` network.
- **Secrets never in Git:** GitHub token, SMTP app password, SonarQube token and Grafana admin password
  are Jenkins credentials, injected with `withCredentials` (masked in logs). Alertmanager writes the SMTP
  password to a private file at start-up (`smtp_auth_password_file`), so it is in neither the image nor the rendered config.
- **Verified inputs:** the full dataset downloaded from the GitHub Release is checked against the
  SHA-256 manifest committed in Git (`src/data/dataset.sha256`) before use.
- **Pinned, hash-verified toolchain:** every Python package (including transitive ones) is installed from
  `src/requirements.lock` with `pip install --require-hashes`; base images are pinned to versions; Trivy,
  hadolint and uv binaries are pinned and SHA-256 verified in `infra/jenkins/Dockerfile`.
- **Metrics exporter on loopback by default:** `telemetry.py` binds to `127.0.0.1`; only the container
  image opts in to `0.0.0.0` (`METRICS_ADDR`), where the port is reachable solely on `devops-net`.

## 3. Findings register

| ID | Tool | Finding | Severity | Decision |
|---|---|---|---|---|
| F-01 | Bandit | Scan of `src/` and `scripts/`: **0 issues** (2026-09-24). A bind-all-interfaces pattern (B104) was designed out: the exporter defaults to `127.0.0.1` and only the container sets `METRICS_ADDR=0.0.0.0`. | - | No action needed; the gate stays active for future code. |
| F-01b | pip-audit | `src/requirements.lock` (all runtime packages): **no known vulnerabilities** (2026-09-24). | - | Re-checked on every build; a new advisory fails the build until the lock is updated or the ID is justified in `.pip-audit-ignore`. |
| F-02 | Code review | Real-looking card numbers and CVVs in the committed `cards_data.csv` | High (data exposure) | **Mitigated.** The dataset is synthetic (public Kaggle data), the columns are dropped at load time and excluded from the sample. Accepted residual risk: the original CSV stays in Git history. For real data the file would be removed from history and stored encrypted. |
| F-03 | Architecture | Jenkins container mounts `/var/run/docker.sock` and runs as root | High (host takeover if Jenkins is compromised) | **Accepted for a single-user lab.** Mitigation: Jenkins only listens on `127.0.0.1`, sign-up disabled, credentials stored in Jenkins. Production alternative: rootless Docker / Kaniko or a dedicated build agent. |
| F-04 | Supply chain | Trivy's own release images and GitHub Actions were compromised in March 2026 (GHSA-69fq-xp46-6x23 / CVE-2026-33634) | Critical (for anyone using affected tags) | **Avoided.** The pipeline never uses Trivy container images or floating tags; it installs the pinned v0.74.0 binary and verifies its SHA-256 in `infra/jenkins/Dockerfile`. |
| F-05 | Trivy image | Base-image OS CVEs (python:3.12-slim / Debian) | varies per build | Reviewed from `trivy-image.txt` each release. Fixable CRITICAL issues fail the build and are fixed by rebuilding with `--pull` (updated base image). Unfixed issues are recorded here with an expiry date in `.trivyignore.yaml` if accepted. |

**Fill in after each scan:** copy the summary line from `reports/security/trivy-image-summary.txt`
and any new Bandit/pip-audit item into this table (what it is, severity, how it was handled).

## 4. Reporting a vulnerability

Please open a private security advisory on the GitHub repository instead of a public issue.
