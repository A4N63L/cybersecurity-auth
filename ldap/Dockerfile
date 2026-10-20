FROM osixia/openldap:1.5.0
# The upstream image is Debian Buster; use its signed archive, not expired mirrors.
RUN printf 'deb http://archive.debian.org/debian buster main\ndeb http://archive.debian.org/debian-security buster/updates main\n' > /etc/apt/sources.list \
    && rm -f /etc/apt/sources.list.d/* \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install -y --no-install-recommends fail2ban iptables \
    && rm -rf /var/lib/apt/lists/*
COPY common/supervise.py /opt/security/supervise.py
COPY ldap/jail.local /etc/fail2ban/jail.local
COPY ldap/ldaps-connections.conf /etc/fail2ban/filter.d/ldaps-connections.conf
COPY ldap/security-processes.json /etc/security-processes.json
COPY ldap/entrypoint.sh /opt/security/entrypoint.sh
COPY ldap/health.py /opt/security/health.py
RUN chmod +x /opt/security/entrypoint.sh
ENV LDAP_TLS=true LDAP_TLS_ENFORCE=true LDAP_TLS_VERIFY_CLIENT=never \
    LDAP_TLS_CA_CRT_FILENAME=ca.crt LDAP_TLS_CRT_FILENAME=ldap.crt LDAP_TLS_KEY_FILENAME=ldap.key \
    LDAP_TLS_DH_PARAM_FILENAME=dhparam.pem LDAPTLS_CACERT=/tls/ca.crt LDAPTLS_REQCERT=demand
ENTRYPOINT ["/opt/security/entrypoint.sh"]
HEALTHCHECK CMD python3 /opt/security/health.py
