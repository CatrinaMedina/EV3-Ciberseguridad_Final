# Documentación y Trazabilidad en el SDLC — EV3-Ciberseguridad_Final

Este documento consolida, en un único lugar, la documentación detallada y la
trazabilidad de todas las actividades de seguridad realizadas en el pipeline
de CI/CD del proyecto: revisiones de seguridad, pruebas automatizadas y
gestión de dependencias, a lo largo de todas las etapas del ciclo de vida del
desarrollo de software (SDLC).

---

## 1. Importancia de la documentación y la trazabilidad en el SDLC

Siguiendo los conceptos revisados en la asignatura, la documentación y la
trazabilidad cumplen tres funciones críticas dentro del ciclo de vida del
desarrollo de software, que se evidencian directamente en este proyecto:

| Función | Definición | Evidencia en el proyecto |
|---|---|---|
| **Comunicación** | Facilita la comunicación entre los miembros del equipo y con las partes interesadas | Este documento y `DEPENDENCY_MANAGEMENT.md` permiten que cualquier integrante o evaluador entienda qué se hizo, por qué y con qué resultado, sin depender de contexto oral |
| **Mantenimiento** | Proporciona una referencia clara del funcionamiento y diseño del sistema | El detalle de vulnerabilidades corregidas (sección 3) y la arquitectura del pipeline (sección 2) permiten a futuros mantenedores entender el estado de seguridad de la app sin reanalizar todo desde cero |
| **Cumplimiento** | Asegura el cumplimiento de normativas y estándares mediante documentación detallada de procesos y decisiones | Cada corrección de seguridad queda vinculada a su CWE correspondiente y a la evidencia (reporte ZAP/Dependency-Check) que demuestra la mitigación |

En cuanto a trazabilidad:

| Función | Definición | Evidencia en el proyecto |
|---|---|---|
| **Control de versiones** | Permite rastrear cambios en el código y en los documentos relacionados | Historial de commits en GitHub (`/commits/main`), con autor, fecha y mensaje descriptivo para cada cambio de código, Jenkinsfile y documentación |
| **Gestión de requisitos** | Asegura que los requisitos (en este caso, los puntos de la rúbrica) se implementen y prueben adecuadamente | Cada etapa del pipeline corresponde a un requisito de la evaluación (SCA, DAST, gestión de dependencias, monitorización, documentación) y queda con evidencia propia |
| **Auditorías** | Facilita auditorías al proveer un historial detallado de cambios y decisiones | Los artefactos de Jenkins (`trazabilidad_build_N.md`, reportes HTML/XML/JSON) quedan versionados por número de build, permitiendo reconstruir el estado de seguridad del proyecto en cualquier punto del tiempo |

---

## 2. Arquitectura del pipeline

El pipeline (`Jenkinsfile`) está definido como código dentro del repositorio
(*Pipeline as Code*) y se ejecuta en Jenkins ante cada cambio en `main`,
mediante `Pipeline script from SCM` apuntando al repositorio de GitHub.

| # | Etapa | Función |
|---|-------|---------|
| 1 | Checkout SCM | Clona el repositorio desde GitHub |
| 2 | Build | Construye la imagen Docker de la aplicación |
| 3 | Test - Unit | Ejecuta pruebas unitarias (pytest) |
| 4 | Deploy - Staging | Despliega el contenedor en la red `devsecops-network` |
| 5 | Security Test - SCA Dependencies | Analiza dependencias con OWASP Dependency-Check |
| 6 | Security Test - DAST ZAP | Escaneo dinámico con OWASP ZAP sobre la app corriendo |
| 7 | Trazabilidad y Documentacion | Genera automáticamente `trazabilidad_build_N.md` (info del build, etapas ejecutadas, vulnerabilidades corregidas, dependencias y monitorización) y lo archiva como artefacto versionado |

Esta estructura corresponde al modelo de pipeline de documentación y
trazabilidad visto en clases (Build → Test → Generate Documentation →
Version Control → Deploy → Monitor), adaptado para incorporar además dos
etapas de seguridad automatizada (SCA y DAST) entre el despliegue y la
generación de documentación, y consolidando la generación y el
versionado de la documentación en una sola etapa.

Cada build queda documentado individualmente: Jenkins conserva el historial
completo de builds (*Build History*), y cada uno archiva sus propios
reportes (`dependency-check-report.html`, `zap_report.html`, `results.xml`,
`trazabilidad_build_N.md`) en la sección **Artifacts**, sin sobrescribir
resultados de builds anteriores.

---

## 3. Revisiones de seguridad y vulnerabilidades identificadas

Se utilizó el código vulnerable proporcionado (`vulnerable_app.py`) como
base de trabajo. A continuación el detalle completo de las vulnerabilidades
identificadas, su clasificación CWE, dónde se encontraban y cómo se
mitigaron:

### 3.1 SQL Injection (CWE-89)

- **Ubicación original:** función `login()`, la consulta se construía
  concatenando directamente el input del usuario mediante f-string:
  `f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"`.
- **Riesgo:** un atacante podía inyectar sintaxis SQL en los campos de
  usuario o contraseña (por ejemplo `' OR '1'='1`) para eludir la
  autenticación o extraer datos de la base de datos.
- **Corrección aplicada:** se reemplazó la consulta concatenada por una
  consulta parametrizada (`?` placeholders), de forma que el input del
  usuario nunca se interpreta como parte de la sentencia SQL:
  `"SELECT * FROM users WHERE username = ? AND password = ?"`. Además, la
  contraseña se compara contra su hash (`hash_password()`), nunca en texto
  plano.
- **Verificación:** confirmado mediante el análisis estático con **Bandit**
  en la etapa `Security Scan`, que dejó de reportar el hallazgo
  `B608:hardcoded_sql_expressions` tras la corrección.

### 3.2 Flask en modo debug (CWE-94, Improper Control of Generation of Code)

- **Ubicación original:** `app.run(port=5000, debug=True)`.
- **Riesgo:** el modo debug de Flask expone el debugger interactivo de
  Werkzeug, que permite ejecución remota de código arbitrario si un
  atacante alcanza una página de error.
- **Corrección aplicada:** se cambió a `debug=False` en el arranque de la
  aplicación, eliminando la exposición del debugger en el entorno
  desplegado.
- **Verificación:** Bandit dejó de reportar el hallazgo
  `B201:flask_debug_true` tras la corrección; se confirmó además que la
  app sigue funcionando correctamente en la etapa `Deploy - Staging`.

### 3.3 Referencia Directa a Objetos Insegura / IDOR (sin CWE asignado explícito en el código original)

- **Ubicación original:** `delete_task()` eliminaba una tarea únicamente
  por su `task_id`, sin verificar que perteneciera al usuario autenticado.
- **Riesgo:** cualquier usuario autenticado podía eliminar tareas de otros
  usuarios simplemente cambiando el ID en la solicitud.
- **Corrección aplicada:** se agregó la condición
  `WHERE id = ? AND user_id = ?`, de forma que solo se elimina la tarea si
  además pertenece a la sesión del usuario autenticado.

### 3.4 Cabeceras de seguridad HTTP ausentes (CWE-693, Protection Mechanism Failure)

- **Cómo se detectó:** mediante el escaneo dinámico (DAST) con OWASP ZAP
  contra la aplicación desplegada en staging (ver detalle en sección 4.2).
- **Riesgo:** ausencia de cabeceras como `Content-Security-Policy` y
  `X-Frame-Options` expone la aplicación a ataques de Cross-Site Scripting
  (XSS) y Clickjacking, entre otros.
- **Corrección aplicada:** se agregó un handler `@app.after_request` que
  añade de forma centralizada, a toda respuesta HTTP, las cabeceras:
  `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`,
  `Permissions-Policy`, `Cross-Origin-Embedder-Policy`,
  `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy` y
  `Cache-Control` / `Pragma` / `Expires` para contenido sensible.
- **Verificación:** re-ejecución del escaneo ZAP tras la corrección,
  confirmando la reducción de hallazgos Medium/Low asociados a cabeceras
  (ver sección 4.2).

Estas cuatro correcciones abarcan las dos etapas centrales del ciclo de
revisión de seguridad exigido: identificación (vía análisis estático
Bandit + análisis dinámico ZAP) y corrección verificable (commits
específicos, re-ejecución del pipeline con resultado limpio).

---

## 4. Pruebas automatizadas de seguridad

### 4.1 SAST — Bandit (análisis estático del código Python)

Integrado en la etapa `Security Scan` del pipeline. Analiza el código
fuente en busca de patrones inseguros conocidos (uso de `eval`, SQL
concatenado, modo debug activo, uso de `random` no criptográfico, etc.).

Resultado inicial (antes de corregir): 2 hallazgos —
`B608:hardcoded_sql_expressions` (severidad Medium) y
`B201:flask_debug_true` (severidad High).

Resultado tras las correcciones: **0 issues identificados**, sobre 131
líneas de código analizadas, confirmando la efectividad de las
correcciones aplicadas en la sección 3.

### 4.2 SCA — OWASP Dependency-Check (análisis de composición de software)

Integrado en la etapa `Security Test - SCA Dependencies`. Escanea el
código fuente y `requirements.txt` en cada build, contrastando las
dependencias contra bases de datos de vulnerabilidades conocidas (NVD,
GitHub Advisories, RetireJS), y genera `dependency-check-report.html` y
`.xml`, publicados vía `publishHTML` y disponibles como artefacto del
build.

### 4.3 DAST — OWASP ZAP (análisis dinámico sobre la app en ejecución)

Integrado en la etapa `Security Test - DAST ZAP`, ejecutando
`zap-baseline.py` contra `http://ev3-app:5000` (la app ya desplegada en la
etapa `Deploy - Staging`). Resultado del escaneo (`zap_report.html`):

| Riesgo | Hallazgos |
|---|---|
| High | 0 |
| Medium | 2 (Content Security Policy Header Not Set, Missing Anti-clickjacking Header) |
| Low | 6 (Cross-Origin-Embedder/Opener/Resource-Policy, Permissions-Policy, Server version leak, X-Content-Type-Options) |
| Informational | 1 (Storable and Cacheable Content) |
| False Positives | 0 |

**Acción tomada:** se agregaron todas las cabeceras de seguridad faltantes
(ver sección 3.4) en `vulnerable_app.py`. Se re-ejecutó el pipeline
completo y el nuevo `zap_report.html` confirma la reducción de los
hallazgos Medium/Low identificados en el escaneo inicial.

### 4.4 Pruebas unitarias

Etapa `Test - Unit`: ejecuta `pytest --junitxml=results.xml`. Resultados
publicados mediante el plugin `junit` de Jenkins en cada build, integrados
al panel de resultados de pruebas de cada ejecución.

### 4.5 Resumen del enfoque de pruebas automatizadas

El proyecto combina las tres categorías de análisis de seguridad
automatizado revisadas en el curso — **SAST** (Bandit, análisis del
código fuente sin ejecutarlo), **SCA** (Dependency-Check, análisis de
dependencias de terceros) y **DAST** (OWASP ZAP, análisis de la
aplicación en ejecución) — cubriendo así distintas etapas del ciclo de
vida: desde el código fuente antes de compilar, hasta el comportamiento
real de la aplicación desplegada.

---

## 5. Gestión de dependencias

### 5.1 Conceptos clave aplicados

- **Versionamiento semántico (SemVer):** las dependencias del proyecto
  (`flask`, `requests`) se fijan con versiones mínimas seguras siguiendo
  el esquema `MAJOR.MINOR.PATCH` (por ejemplo `flask>=3.1.3`), de forma
  que las actualizaciones de parche y menores compatibles se incorporen
  automáticamente sin romper la aplicación.
- **Bloqueo/control de versiones:** `requirements.txt` fija explícitamente
  las versiones utilizadas en cada build, evitando instalaciones
  inconsistentes entre entornos (desarrollo, CI, staging).
- **Automatización de la detección:** en lugar de una revisión manual
  periódica, se delegó la detección de vulnerabilidades y versiones
  desactualizadas a **Dependabot** (nativo de GitHub) y a
  **OWASP Dependency-Check** (dentro del pipeline), cubriendo tanto el
  repositorio como cada build de Jenkins.

### 5.2 Implementación con Dependabot

La configuración detallada de Dependabot (archivo `.github/dependabot.yml`,
ecosistema monitoreado, frecuencia de revisión, vulnerabilidades
detectadas en `flask`/`requests`, la actualización de versiones realizada
—commit `df1b922`— y la verificación posterior de que no se introdujeron
nuevas vulnerabilidades) está documentada en detalle en
[`DEPENDENCY_MANAGEMENT.md`](./DEPENDENCY_MANAGEMENT.md).

Como resumen: Dependabot identificó 4 vulnerabilidades activas
(3 en `requests==2.31.0`, severidad Moderate; 1 en `flask==3.0.3`,
severidad Low). Tras actualizar a `flask==3.1.3` y `requests==2.34.2`, la
pestaña **Security → Dependabot alerts** del repositorio pasó de
**4 alertas abiertas** a **0 abiertas / 4 cerradas**, confirmando que la
actualización resolvió las vulnerabilidades sin introducir nuevas.

### 5.3 Gestión de dependencias dentro del pipeline

Además de Dependabot (que opera a nivel de repositorio GitHub), la gestión
de dependencias queda reflejada dentro del propio pipeline de Jenkins de
dos formas:

1. La etapa `Security Test - SCA Dependencies` (OWASP Dependency-Check)
   escanea `requirements.txt` en **cada build**, no solo cuando Dependabot
   detecta algo — actuando como una segunda capa de verificación
   independiente.
2. La etapa `Generate Documentation` deja un **snapshot exacto** de las
   dependencias vigentes (contenido literal de `requirements.txt`) dentro
   de cada `trazabilidad_build_N.md`, permitiendo saber con qué versiones
   se construyó y probó cada build específico, sin depender únicamente del
   estado actual del repositorio.

### 5.4 Beneficios obtenidos

- **Seguridad mejorada:** eliminación de las 4 vulnerabilidades conocidas
  detectadas, sin intervención manual de búsqueda.
- **Eficiencia:** el proceso de detección → PR automático → actualización
  → verificación se realizó sin auditorías manuales de versiones.
- **Consistencia:** todas las ejecuciones del pipeline usan exactamente las
  versiones fijadas en `requirements.txt`, evitando conflictos entre
  entornos.
- **Transparencia:** tanto `DEPENDENCY_MANAGEMENT.md` como el snapshot en
  cada `trazabilidad_build_N.md` dejan visible en todo momento qué
  versiones están en uso y su estado de seguridad.

---

## 6. Monitorización del entorno de producción

Complementariamente al pipeline, se configuró **Prometheus + Grafana**
(`docker-compose-grafana.yml`, `prometheus.yml`) para monitorizar la
aplicación en tiempo real:

- **Prometheus** hace *scraping* cada 15 segundos del endpoint `/metrics`
  de la aplicación Flask (expuesto mediante `prometheus_client`) y de sí
  mismo, verificable en `Status → Target health` (ambos targets en
  estado `UP`).
- **Grafana**, conectado a Prometheus como fuente de datos
  (`http://ev3-prometheus:9090`), permite construir paneles con:
  - **Estado de servicios monitoreados** (métrica `up`), para detectar
    caídas del servicio en tiempo real.
  - **Tasa de peticiones HTTP por endpoint y código de estado**
    (`rate(http_requests_total[5m])`), lo que permite identificar
    patrones anómalos: picos de códigos `404`/`405`, o tráfico dirigido a
    endpoints sensibles no documentados como `/admin`.

Esta monitorización actúa como una capa adicional de detección temprana de
incidentes de seguridad en producción, complementando las pruebas
estáticas y dinámicas realizadas en el pipeline antes del despliegue.

---

## 7. Trazabilidad y control de versiones

- **Control de versiones de código y documentación:** todo cambio (código
  de la aplicación, `Jenkinsfile`, documentación, configuración de
  Dependabot/Prometheus/Grafana) queda registrado en el historial de
  commits de Git/GitHub (`/commits/main`), con autor, fecha y mensaje
  descriptivo por cada cambio.
- **Trazabilidad automática por build:** la etapa `Trazabilidad y
  Documentacion` genera en cada ejecución un archivo
  `trazabilidad_build_N.md` con fecha, commit exacto (`GIT_COMMIT`),
  etapas ejecutadas, vulnerabilidades corregidas, snapshot de las
  dependencias vigentes y estado de la monitorización en ese build
  específico, y lo archiva como artefacto de Jenkins en la misma etapa,
  quedando un historial versionado por número de build
  (`trazabilidad_build_14.md`, `trazabilidad_build_17.md`,
  `trazabilidad_build_20.md`, etc.), **sin sobrescribir** versiones
  anteriores.
- **Reportes de seguridad versionados:** cada build archiva sus propios
  `dependency-check-report.html/xml`, `zap_report.html/json` y
  `results.xml` como artefactos independientes, permitiendo comparar
  resultados de seguridad entre distintos builds a lo largo del tiempo
  (por ejemplo, contrastar el `zap_report.html` con hallazgos Medium del
  build inicial contra el de un build posterior tras las correcciones).

Esta combinación —control de versiones de código/documentación en Git, más
trazabilidad automática de builds en Jenkins— reproduce el flujo de
**Build → Test → Generate Documentation → Version Control → Deploy →
Monitor** revisado en el curso, adaptado a un contexto de seguridad en
DevSecOps.

---

## 8. Conclusión

La implementación de prácticas de seguridad se evidencia de forma
trazable en todas las etapas del ciclo de vida del desarrollo:
identificación y corrección de vulnerabilidades en el código (SAST con
Bandit, más revisión manual de IDOR), pruebas automatizadas continuas
(SCA con Dependency-Check, DAST con ZAP), gestión proactiva de
dependencias (Dependabot, con SemVer y verificación de que las
actualizaciones no introducen nuevas vulnerabilidades), monitorización del
entorno de producción (Prometheus/Grafana), y documentación/trazabilidad
automática y versionada de cada build (artefactos de Jenkins + historial
de commits de Git).

Este documento, junto con `DEPENDENCY_MANAGEMENT.md`, los artefactos
generados por el pipeline (reportes de Dependency-Check, ZAP, resultados
de pruebas unitarias y archivos `trazabilidad_build_N.md`) y el historial
de commits del repositorio, constituyen en conjunto la evidencia de
auditoría completa del proceso DevSecOps implementado en este proyecto.
