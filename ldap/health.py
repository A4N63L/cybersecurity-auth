import os
import subprocess
import tempfile

subprocess.run(['fail2ban-client', 'ping'], check=True, stdout=subprocess.DEVNULL)
with tempfile.NamedTemporaryFile(mode='w') as password:
    password.write(os.environ['LDAP_ADMIN_PASSWORD'])
    password.flush()
    subprocess.run(['ldapsearch', '-x', '-H', 'ldaps://openldap:636', '-D',
                    'cn=admin,dc=example,dc=com', '-y', password.name,
                    '-b', 'dc=example,dc=com', '-s', 'base'],
                   check=True, stdout=subprocess.DEVNULL)
