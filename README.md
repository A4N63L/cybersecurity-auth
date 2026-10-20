# GameVault · Autenticación, LDAPS y configuración común de Fail2Ban

Proyecto local `videojuegos-auth`, hermano de frontend y backend. Única fuente de
configuración de Keycloak, OpenLDAP, su PostgreSQL y los componentes de seguridad
compartidos. No contiene credenciales, datos ni certificados generados.

## Arranque integrado

Desde `../videojuegos-backend`: `bash lab.sh up`. No levantes este fragmento de
Compose de forma independiente: el lanzador conserva el proyecto `ciber-p1-games`,
red `lab`, volúmenes y datos existentes, e inyecta rutas absolutas.

- `compose.yaml`: OpenLDAP, ldap-init, PostgreSQL, Keycloak y auth-migrate.
- `common/`: supervisor PID 1, healthcheck y jail/filtro HTTP.
- `keycloak/`: imagen, configuración/import inicial y migración online del realm.
- `ldap/`: imagen sobre OpenLDAP 1.5.0, inicializador, TLS y jail de conexiones.

Keycloak conserva `start-dev` y HTTP publicado en `127.0.0.1:8082`. Su
distribución oficial 26.7.4 se ejecuta con Java 21 sobre Debian Trixie para disponer
de paquetes compatibles de Fail2Ban/iptables. Java corre como usuario `keycloak`;
Fail2Ban y el supervisor conservan los permisos necesarios para el firewall.
OpenLDAP conserva su versión y bootstrap original para no cambiar el formato
de las bases existentes. Instala Fail2Ban/iptables desde el archivo firmado Buster.

## TLS reproducible y migración sin borrar datos

`lab.sh up` ejecuta:

```bash
python3 ../videojuegos-auth/generate_tls.py "$PWD/.lab-data/tls"
```

Genera una CA RSA 3072, certificado servidor con SAN **DNS:openldap**, EKU
serverAuth y parámetros DH ffdhe2048. Preserva todos los archivos existentes y
rechaza un conjunto parcial. Las claves tienen permisos 600, el directorio 700.
La CA dura 10 años y el certificado servidor 825 días; comprueba su vencimiento
antes de renovar. Guarda una copia privada de `.lab-data/tls`, especialmente
`ca.key`; para regenerar certificados de una instalación, haz primero un respaldo
y vuelve a firmar el certificado con su CA, sin sobrescribirla accidentalmente.

Solo `ca.crt` se monta en Keycloak/ldap-init. OpenLDAP recibe certificado, clave,
CA y DH, pero **no la clave de la CA**. La clave del servidor se copia a la ruta
privada que administra el bootstrap de la imagen y se asigna a `openldap`.

El bootstrap aplica mediante LDAP EXTERNAL sobre `ldapi:///` la configuración TLS
al `cn=config` persistido; vuelve a hacerlo al recrear el contenedor. El proceso
final escucha únicamente en **636 y ldapi**, no en 389. Además se activa
`LDAP_TLS_ENFORCE=true`. `LDAP_TLS_VERIFY_CLIENT=never` significa que el servidor
no exige certificados a sus clientes: **no desactiva la validación del servidor**.
Los clientes usan `LDAPTLS_REQCERT=demand` y su CA.

Keycloak usa `KC_TRUSTSTORE_PATHS=/tls/ca.crt` y el proveedor LDAP conecta a
`ldaps://openldap:636`, StartTLS false, truststore always. No se desactiva la
comprobación de nombre de Java/JNDI. `keycloak/migrate.py` modifica exclusivamente
ese proveedor en el realm existente mediante API administrativa; conserva ID,
usuarios, cliente y resto de configuración. No imprime respuestas con secretos.

El JSON de importación cubre instalaciones nuevas. La migración idempotente
`auth-migrate` cubre el realm persistido y bloquea el arranque del frontend si falla.
Para repetirla manualmente:

```bash
bash lab.sh run --rm auth-migrate
```

`ldap-init` verifica los binds por LDAPS y solo añade las entradas que falten;
no rota contraseñas existentes. La raíz administrativa y los usuarios permanecen.

## Protección independiente de LDAP

Jail **`ldaps-connections`**: **60 conexiones por IP en 10 s**, veto de **10 min**,
acción `iptables-multiport` limitada a **TCP/636** en INPUT del contenedor.
No hay jail de contraseñas fallidas.

`slapd -d 256` produce eventos reales ACCEPT. El supervisor conserva esos eventos,
añade fecha legible y los escribe en `/var/log/security/access.log`. El filtro
exige `conn=... fd=... ACCEPT from IP=<HOST>:... (IP=...:636)`. No analiza HTTP ni
infiere la IP del navegador: para LDAP, Keycloak es el cliente.

Las jails HTTP de las otras tres imágenes usan 60 peticiones/10 s, 10 min iniciales
y escalado por reincidencia hasta 1 día. No se ignora la subred del laboratorio ni
se añade Keycloak a una lista blanca. El pool normal de conexiones no produjo vetos.

## Respaldo y restauración

Antes de la primera migración se hizo un **respaldo en frío verificado**, fuera
de Git, en:

```text
../.lab-backups/20261019-194554/
├── lab-before-tls.tar
└── manifest.json
```

Incluye `.lab-data` completa (LDAP datos/configuración, PostgreSQL y SQLite),
`.env`, ambos Compose anteriores, `lab.sh` e `infra/` anterior. El directorio es
privado y el archivo tiene permisos 600. El manifest identifica el daemon y los
IDs de imagen; **no contiene las imágenes**. Los antiguos tags `:pre-fail2ban`
se perdieron al reiniciar el almacenamiento temporal. `rollback-images.tar.gz`
quedó en cero bytes y **no es un respaldo válido**. No se usa para recuperar.

La recuperación conserva el código actual y reconstruye sus imágenes. No extraigas
el tar encima de `.lab-data`, ni sustituyas los Compose actuales por los anteriores.

Procedimiento desde el backend, con el laboratorio detenido:

```bash
sudo -n python3 scripts/recover_data.py prepare
```

Genera un directorio privado `../.lab-backups/recovery-<fecha>/` con:

- `current-state.tar`: estado previo a intervenir, incluidos `.env`, certificados
  y claves actuales; verificación del índice del tar.
- `original-extracted/`: extracción **independiente** del respaldo original,
  conservando propietarios y permisos.
- `inventory.json`: SQLite integrity_check, conteos, PG_VERSION, estructura,
  propietarios y comparación de archivos; no incluye secretos.

En esta recuperación se usó `recovery-20261019-203712`: el PostgreSQL actual estaba
presente (UID/GID 70, modo 700, versión 16), igual que LDAP, TLS y **11 juegos**.
El respaldo anterior contiene 8 juegos y LDAP sin TLS. Por tanto se conservan
los datos actuales, evitando retroceder el realm y perder las altas posteriores.

Solo si faltase el cluster actual completo, después de verificar y apartar los
datos anteriores, se puede usar:

```bash
sudo -n python3 scripts/recover_data.py restore-postgres ../.lab-backups/recovery-<fecha>
```

Ese modo rechaza un PGDATA no vacío, conserva aparte un directorio vacío previo,
copia **todo** el cluster original y compara sus archivos. Nunca mezcla `base`,
`pg_wal`, `global` u otros componentes de clusters distintos. Usa PostgreSQL **16**.
Para LDAP se recuperan siempre el par datos/configuración de la misma copia con
OpenLDAP 1.5.0. No copies bases mientras estén en ejecución. Los certificados
actuales se conservan salvo que su propia validación exija recuperarlos.

Después, `bash lab.sh up` conserva el código TLS actual y aplica las migraciones
idempotentes LDAP/realm. No se necesita borrar ni reinicializar bases.

Validación funcional de la copia aislada y comparación con el lab activo:

```bash
sudo -n python3 tests/recovery_checks.py ../.lab-backups/recovery-20261019-203712
```

Comprueba SQLite, preservación exacta de los TLS actuales, lectura `slapcat` de
ambos directorios LDAP y hashes de usuarios. Inicia **solo la copia extraída** de
PostgreSQL 16 sin red y compara IDs de realm, cliente y proveedor con el servicio
actual; el archivo original permanece intacto. El resultado se guarda en
`verified.json` privado y `test-results/recovery.json` saneado.

Para futuros respaldos fríos, el backend incluye `scripts/backup_lab.py`: selecciona
el daemon mediante `lab.sh`, detiene los cinco servicios y los vuelve a arrancar
al terminar; protege los archivos fuera de Git. Las imágenes reconstruibles residen
ahora en el almacén persistente `.lab-docker`; no se intenta archivar imágenes viejas.

## Verificación

Desde el backend: `python3 tests/security_checks.py` y
`/tmp/opencode/browser-venv/bin/python tests/browser_demo.py`.
El primero comprueba certificado/nombre, rechazo sin CA, cierre de 389, las cuatro
jails con clientes distintos y recuperación al desbanear. Reutiliza la red
existente: no crea la subred del ZIP ni contenedores permanentes de carga.
