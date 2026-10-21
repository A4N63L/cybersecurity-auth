# Análisis con Nuclei — Autenticación

Análisis no intrusivo de vulnerabilidades conocidas y configuraciones expuestas sobre los dos servicios de autenticación del laboratorio. Esta entrega solo **enumera** los hallazgos; no aplica correcciones.

| Servicio | Dirección | critical | high | medium |
|---|---|---|---|---|
| Keycloak (autenticación HTTP) | `http://172.29.0.5:8080` | 0 | 0 | 0 |
| OpenLDAP (LDAPS 636) | `ldaps://172.29.0.3:636` | 0 | 0 | 1 |

## Keycloak (autenticación HTTP)

- **Fecha (UTC):** 2026-10-21 05:14
- **Servicio:** Keycloak (autenticación HTTP)
- **Dirección analizada:** `http://172.29.0.5:8080` (resuelta en el contenedor como `http://keycloak:8080`)
- **Herramienta:** Nuclei v3.11.1, imagen oficial `projectdiscovery/nuclei` pinneada por digest
- **Plantillas:** snapshot oficial `projectdiscovery/nuclei-templates` en commit `b4826535d814f33522faae784678e62686d33b66`, filtradas a severidades `medium,high,critical`; sin tags `dos`, `fuzz` ni `bruteforce`
- **Finalización verificada:** código de salida `0`, `Scan completed` presente, duración 738.2 s
- **Resultado:** 0 hallazgo(s) — critical: 0, high: 0, medium: 0

### Comando ejecutado

```
docker exec nuclei-initial-assessment nuclei -u http://keycloak:8080 -severity medium,high,critical -t /work/keycloak.templates.txt -pt http -duc -dut -ni -nh -no-stdin -dr -nc -or -ot -rl 4 -c 1 -bs 1 -pc 1 -jsc 1 -tlc 1 -timeout 5 -retries 0 -mhe 10 -max-time 30m -stats -si 10 -vv -rsr 1048576 -jle /work/raw/keycloak.jsonl -tlog /work/raw/keycloak.trace.jsonl -elog /work/raw/keycloak.errors.txt
```

### Hallazgos

Sin hallazgos para las plantillas y severidades ejecutadas.

### Errores registrados

```
{"template":"/root/nuclei-templates/http/misconfiguration/apachespark-ui-exposed.yaml","type":"http","input":"http://keycloak:4040/jobs/","address":"keycloak:4040","error":"port closed or filtered","kind":"network-permanent-error","attrs":{}}
{"template":"/root/nuclei-templates/http/misconfiguration/microsoft/anonymous-distribution-point-sccm.yaml","type":"http","input":"http://keycloak:80/SMS_DP_SMSPKG$/Datalib","address":"keycloak:80","error":"port closed or filtered","kind":"network-permanent-error","attrs":{}}
```


## OpenLDAP (LDAPS 636)

- **Fecha (UTC):** 2026-10-21 04:55
- **Servicio:** OpenLDAP (LDAPS 636)
- **Dirección analizada:** `ldaps://172.29.0.3:636` (resuelta en el contenedor como `openldap:636`)
- **Herramienta:** Nuclei v3.11.1, imagen oficial `projectdiscovery/nuclei` pinneada por digest
- **Plantillas:** snapshot oficial `projectdiscovery/nuclei-templates` en commit `b4826535d814f33522faae784678e62686d33b66`, filtradas a severidades `medium,high,critical`; sin tags `dos`, `fuzz` ni `bruteforce`
- **Finalización verificada:** código de salida `0`, `Scan completed` presente, duración 2.0 s
- **Resultado:** 1 hallazgo(s) — critical: 0, high: 0, medium: 1

### Comando ejecutado

```
docker exec nuclei-initial-assessment nuclei -u openldap:636 -severity medium,high,critical -t /work/ldaps.templates.txt -pt javascript -duc -dut -ni -nh -no-stdin -dr -nc -or -ot -rl 3 -c 1 -bs 1 -pc 1 -jsc 1 -tlc 1 -timeout 5 -retries 0 -mhe 10 -max-time 30m -stats -si 10 -vv -rsr 1048576 -jle /work/raw/ldaps.jsonl -tlog /work/raw/ldaps.trace.jsonl -elog /work/raw/ldaps.errors.txt -sni openldap
```

### Hallazgos

| Severidad | Plantilla | Nombre | Coincidencia |
|---|---|---|---|
| medium | `ldap-anonymous-login-detect` | LDAP Anonymous Login - Detect | `openldap:636` |


### Notas de alcance y limitaciones

- Se ejecutaron únicamente plantillas oficiales de Nuclei, con severidades `medium`, `high` y `critical`.
- Las plantillas `ssl/*` del snapshot oficial son de severidad `info`/`low`; por el filtro de severidad solicitado no se ejecutaron. Las plantillas LDAP `default-login` y `metadata` también son `info` y quedaron fuera. Se documenta como cobertura no incluida en esta pasada.
- En OpenLDAP solo se comprobó el puerto LDAPS/636 (el 389 está cerrado). La comprobación principal fue el bind anónimo permitido.
- No se realizaron pruebas autenticadas, fuzzing, fuerza bruta ni pruebas de denegación de servicio.
- Se limitó la tasa a 3–4 peticiones por segundo y se mantuvieron las protecciones de Fail2Ban activas y sin cambios; no se produjeron bloqueos durante la ejecución.
- No se siguieron redirecciones HTTP ni se enviaron datos de explotación.
- Los resultados reflejan exclusivamente lo observable en la fecha indicada; no sustituyen una revisión manual ni un análisis autenticado.
- Los archivos JSONL contienen la evidencia cruda de Nuclei y no incluyen cuerpos de petición/respuesta ni credenciales.

### Evidencia de ejecución

Ambos procesos terminaron con código `0` y sus logs conservan la línea de finalización de Nuclei. El detalle operativo está en `keycloak-nuclei-execution.txt` y `ldaps-nuclei-execution.txt`; los resultados en los JSONL correspondientes.

