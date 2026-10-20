"""Update only the LDAP provider of the existing realm. No exports or secrets logged."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://keycloak:8080'


def main():
    credentials = urllib.parse.urlencode({'client_id': 'admin-cli', 'grant_type': 'password',
        'username': 'admin', 'password': os.environ['KEYCLOAK_ADMIN_PASSWORD']}).encode()
    with urllib.request.urlopen(BASE + '/realms/master/protocol/openid-connect/token', credentials) as response:
        token = json.load(response)['access_token']

    def api(path, method='GET', data=None):
        request = urllib.request.Request(BASE + '/admin/realms/games-lab/' + path,
            method=method, data=json.dumps(data).encode() if data is not None else None,
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request) as response:
            body = response.read()
            return json.loads(body) if body else None

    providers = [item for item in api('components?type=org.keycloak.storage.UserStorageProvider')
                 if item['providerId'] == 'ldap' and item['name'] == 'games-openldap']
    assert len(providers) == 1, 'Expected exactly one existing LDAP provider'
    component = providers[0]
    expected = {'connectionUrl': ['ldaps://openldap:636'], 'startTls': ['false'],
                'useTruststoreSpi': ['always']}
    if any(component['config'].get(key) != value for key, value in expected.items()):
        component['config'].update(expected)
        # Keycloak masks the old secret in GET responses. Supply its unchanged private value.
        component['config']['bindCredential'] = [os.environ['LDAP_ADMIN_PASSWORD']]
        api('components/' + component['id'], 'PUT', component)
    saved = api('components/' + component['id'])
    assert all(saved['config'].get(key) == value for key, value in expected.items())
    print('LDAP provider verified: LDAPS with truststore; realm and users preserved.')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as error:
        raise SystemExit('Keycloak migration HTTP status: ' + str(error.code)) from None
