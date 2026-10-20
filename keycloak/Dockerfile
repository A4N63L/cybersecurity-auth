FROM quay.io/keycloak/keycloak:26.7.4 AS upstream
FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-21-jre-headless python3 fail2ban iptables ca-certificates util-linux && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 keycloak && useradd -u 1000 -g 1000 -d /opt/keycloak keycloak
COPY --from=upstream --chown=1000:1000 /opt/keycloak /opt/keycloak
COPY common/ /opt/security/
COPY common/jail.local /etc/fail2ban/jail.local
COPY common/http-flood.conf /etc/fail2ban/filter.d/http-flood.conf
COPY keycloak/jail.local /etc/fail2ban/jail.d/keycloak.local
COPY keycloak/security-processes.json /etc/security-processes.json
RUN mkdir -p /opt/keycloak/data/log && touch /opt/keycloak/data/log/keycloak-http-access.log && chown -R keycloak:keycloak /opt/keycloak/data
ENV ACCESS_LOG=/opt/keycloak/data/log/keycloak-http-access.log HEALTH_URL=http://127.0.0.1:9000/health/ready
EXPOSE 8080 9000
ENTRYPOINT ["python3", "/opt/security/supervise.py"]
HEALTHCHECK CMD python3 /opt/security/health.py
