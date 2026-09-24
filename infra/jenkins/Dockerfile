# Jenkins controller with the CLI tools the pipeline needs (Docker CLI + Compose, uv, Trivy, jq).
FROM jenkins/jenkins:lts-jdk21

USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Docker CLI, Buildx and Compose from Docker's official apt repository
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl gnupg jq shellcheck \
 && install -m 0755 -d /etc/apt/keyrings \
 && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
 && chmod a+r /etc/apt/keyrings/docker.asc \
 && . /etc/os-release \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian ${VERSION_CODENAME} stable" \
      > /etc/apt/sources.list.d/docker.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin docker-compose-plugin \
 && rm -rf /var/lib/apt/lists/*

# uv: fast Python installer; it also downloads Python 3.12 for the test virtualenv
COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /uvx /usr/local/bin/

# hadolint (Dockerfile linter): pinned binary verified by SHA-256
ARG HADOLINT_VERSION=2.15.1
ARG HADOLINT_SHA256_AMD64=c7187db94eeeeca956519a6af171adc31453941a1e777961f6e680f697c8c507
ARG HADOLINT_SHA256_ARM64=f6198ef8090f404dbb771abfee086eb8c48ac177f30da7fd3510aca35b344b5d
RUN case "$(dpkg --print-architecture)" in \
      amd64) asset="x86_64"; sha="${HADOLINT_SHA256_AMD64}" ;; \
      arm64) asset="arm64"; sha="${HADOLINT_SHA256_ARM64}" ;; \
      *) echo "unsupported architecture" >&2; exit 1 ;; \
    esac \
 && curl -fsSL -o /usr/local/bin/hadolint \
      "https://github.com/hadolint/hadolint/releases/download/v${HADOLINT_VERSION}/hadolint-linux-${asset}" \
 && echo "${sha}  /usr/local/bin/hadolint" | sha256sum -c - \
 && chmod 0755 /usr/local/bin/hadolint \
 && hadolint --version

# Trivy: pinned release binary verified by SHA-256.
# Never use a floating tag: Trivy's own images/actions were compromised in March 2026
# (GHSA-69fq-xp46-6x23 / CVE-2026-33634). Checksums from trivy_0.74.0_checksums.txt.
ARG TRIVY_VERSION=0.74.0
ARG TRIVY_SHA256_AMD64=2ae6fe3ee734b7fdf11335663e18c75ea12dccc76062f09f164a3b0f8be4371a
ARG TRIVY_SHA256_ARM64=b94ce1976bbf3c15b514b605ee88be7c6d94a29be2302847ff01cb794d47aad5
RUN case "$(dpkg --print-architecture)" in \
      amd64) asset="Linux-64bit"; sha="${TRIVY_SHA256_AMD64}" ;; \
      arm64) asset="Linux-ARM64"; sha="${TRIVY_SHA256_ARM64}" ;; \
      *) echo "unsupported architecture" >&2; exit 1 ;; \
    esac \
 && curl -fsSL -o /tmp/trivy.tar.gz \
      "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_${asset}.tar.gz" \
 && echo "${sha}  /tmp/trivy.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/trivy.tar.gz -C /usr/local/bin trivy \
 && rm /tmp/trivy.tar.gz \
 && trivy --version

USER jenkins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

ENV UV_CACHE_DIR=/var/jenkins_home/.cache/uv \
    UV_PYTHON_INSTALL_DIR=/var/jenkins_home/.local/share/uv/python \
    TRIVY_CACHE_DIR=/var/jenkins_home/.cache/trivy

USER jenkins
