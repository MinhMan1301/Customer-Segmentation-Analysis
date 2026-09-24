FROM grafana/grafana:12.4.11
COPY provisioning/ /etc/grafana/provisioning/
COPY dashboards/ /etc/grafana/dashboards/
USER 472
HEALTHCHECK --interval=15s --timeout=5s CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:3000/api/health"]
