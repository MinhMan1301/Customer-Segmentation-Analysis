FROM prom/alertmanager:v0.34.1
COPY alertmanager.yml.tmpl /etc/alertmanager/alertmanager.yml.tmpl
COPY entrypoint.sh /etc/alertmanager/entrypoint.sh
USER 65534:65534
HEALTHCHECK --interval=15s --timeout=5s CMD ["wget", "-q", "--spider", "http://127.0.0.1:9093/-/ready"]
ENTRYPOINT ["/bin/sh", "/etc/alertmanager/entrypoint.sh"]
