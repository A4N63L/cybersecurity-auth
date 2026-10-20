"""Generate once; never replace existing CA/key. Files remain in ignored .lab-data."""
import os
from pathlib import Path
import subprocess
import sys

directory = Path(sys.argv[1]).resolve()
directory.mkdir(mode=0o700, parents=True, exist_ok=True)
names = ['ca.key', 'ca.crt', 'ldap.key', 'ldap.crt', 'dhparam.pem']
if all((directory / name).is_file() for name in names):
    print('Existing TLS material preserved.')
    sys.exit(0)
if any((directory / name).exists() for name in names):
    raise SystemExit('Partial TLS material: recover it before generating; refusing to overwrite.')
os.umask(0o077)


def openssl(*args):
    subprocess.run(['openssl', *args], cwd=directory, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


openssl('req', '-x509', '-newkey', 'rsa:3072', '-nodes', '-sha256', '-days', '3650',
        '-subj', '/CN=Games Lab LDAP CA', '-keyout', 'ca.key', '-out', 'ca.crt',
        '-addext', 'basicConstraints=critical,CA:TRUE', '-addext', 'keyUsage=critical,keyCertSign,cRLSign')
openssl('req', '-newkey', 'rsa:3072', '-nodes', '-sha256', '-subj', '/CN=openldap',
        '-keyout', 'ldap.key', '-out', 'ldap.csr')
extensions = directory / 'server.ext'
extensions.write_text('subjectAltName=DNS:openldap\nbasicConstraints=critical,CA:FALSE\n'
                      'keyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n')
openssl('x509', '-req', '-in', 'ldap.csr', '-CA', 'ca.crt', '-CAkey', 'ca.key',
        '-CAcreateserial', '-days', '825', '-sha256', '-extfile', 'server.ext', '-out', 'ldap.crt')
openssl('genpkey', '-genparam', '-algorithm', 'DH', '-pkeyopt', 'group:ffdhe2048', '-out', 'dhparam.pem')
for name in ('ca.crt', 'ldap.crt', 'dhparam.pem'):
    (directory / name).chmod(0o644)
print('TLS material generated; SAN DNS:openldap. Private keys remain local.')
