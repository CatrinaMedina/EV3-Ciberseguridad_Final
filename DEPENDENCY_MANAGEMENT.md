# Gestión de Dependencias — EV3-Ciberseguridad_Final

## 1. Configuración de Dependabot

Se implementó Dependabot en el repositorio mediante el archivo `.github/dependabot.yml`,
configurado para monitorear el ecosistema `pip` en el directorio raíz del proyecto,
con revisiones semanales:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

Con esta configuración, GitHub habilitó automáticamente:
- **Dependabot alerts**: notificaciones de vulnerabilidades conocidas en las dependencias.
- **Dependabot security updates**: creación automática de ramas/PRs con las versiones
  corregidas (ej. `dependabot/pip/flask-gte-3.1.3`, `dependabot/pip/requests-2.33.0`,
  `dependabot/pip/requests-2.34.2`).

## 2. Vulnerabilidades detectadas

Antes de la actualización, `requirements.txt` contenía:

```
flask==3.0.3
requests==2.31.0
```

Dependabot identificó 4 vulnerabilidades activas asociadas a estas versiones:

| Paquete  | Vulnerabilidad                                                        | Severidad |
|----------|------------------------------------------------------------------------|-----------|
| requests | Leak de credenciales `.netrc` vía URLs maliciosas                     | Moderate  |
| requests | El objeto `Session` no vuelve a verificar tras usar `verify=False`    | Moderate  |
| requests | Insecure Temp File Reuse en `extract_zipped_paths()`                  | Moderate  |
| flask    | La sesión no agrega el header `Vary: Cookie` en ciertos accesos       | Low       |

## 3. Actualización realizada

Se actualizó `requirements.txt` a las versiones mínimas seguras indicadas por Dependabot:

```
flask==3.1.3
requests==2.34.2
```

Cambio aplicado en el commit `df1b922` ("Update requirements.txt").

## 4. Verificación de que no se introdujeron nuevas vulnerabilidades

Tras el commit, GitHub volvió a analizar automáticamente las dependencias
("Dependency files checked... for commit df1b922"), confirmando:

- **0 alertas abiertas** (0 Open / 4 Closed) en Dependabot → Vulnerabilities.
- No se generaron nuevas alertas de Dependabot tras la actualización.
- Se re-ejecutó el pipeline de Jenkins (`EV3-Pipeline_Final`) con las nuevas versiones,
  validando que la etapa `Security Scan` (Bandit + Safety) se ejecutara correctamente
  y sin errores de compatibilidad, confirmando que la actualización no rompió la
  aplicación ni introdujo hallazgos nuevos.

## 5. Conclusión

El proceso de gestión de dependencias se realizó de forma trazable: detección automática
(Dependabot) → actualización manual dirigida por las recomendaciones del propio Dependabot
→ verificación posterior (cierre de alertas + re-ejecución del pipeline). Esto asegura que
las dependencias del proyecto se mantienen libres de vulnerabilidades conocidas sin afectar
la funcionalidad de la aplicación.
