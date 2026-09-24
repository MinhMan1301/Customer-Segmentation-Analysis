#!/bin/sh
# Render the Alertmanager config from environment variables (SMTP credentials come from
# Jenkins credentials at deploy time and are never stored in Git or in the image), then start.
set -eu
: "${SMTP_USER:?SMTP_USER is required}"
: "${SMTP_PASSWORD:?SMTP_PASSWORD is required}"
: "${ALERT_EMAIL_TO:?ALERT_EMAIL_TO is required}"

escape() { printf '%s' "$1" | sed -e 's/[|&\\]/\\&/g'; }

umask 077
# The password goes to a private file (any characters allowed), never through sed or YAML.
printf '%s' "$SMTP_PASSWORD" > /tmp/smtp_password
sed -e "s|__SMTP_USER__|$(escape "$SMTP_USER")|g" \
    -e "s|__ALERT_EMAIL_TO__|$(escape "$ALERT_EMAIL_TO")|g" \
    /etc/alertmanager/alertmanager.yml.tmpl > /tmp/alertmanager.yml

exec /bin/alertmanager --config.file=/tmp/alertmanager.yml --storage.path=/alertmanager "$@"
