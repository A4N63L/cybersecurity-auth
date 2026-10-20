#!/bin/bash
set -euo pipefail
certs=/container/service/slapd/assets/certs
cp /tls/ca.crt /tls/ldap.crt /tls/ldap.key /tls/dhparam.pem "$certs/"
# Preserve upstream bootstrap, including its online/idempotent cn=config TLS update.
/container/tool/run --run-only startup --no-kill-all-on-exit
ulimit -n 1024
exec python3 /opt/security/supervise.py
