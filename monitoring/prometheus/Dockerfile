FROM prom/prometheus:v3.13.3
COPY prometheus.yml alert_rules.yml alert_rules_test.yml /etc/prometheus/
USER 65534:65534
HEALTHCHECK --interval=15s --timeout=5s CMD ["wget", "-q", "--spider", "http://127.0.0.1:9090/-/ready"]
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--storage.tsdb.retention.time=15d", \
     "--web.enable-lifecycle"]
