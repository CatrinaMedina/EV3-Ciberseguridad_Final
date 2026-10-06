# EV3-Ciberseguridad_Final

## Descripción

Este proyecto corresponde a la implementación de un entorno DevSecOps,
integrando prácticas de seguridad dentro del ciclo de vida del desarrollo
de software (SDLC). El objetivo es automatizar el proceso de desarrollo,
pruebas y despliegue, incorporando controles de seguridad, gestión de
dependencias, monitorización y trazabilidad de manera continua, de forma
que la seguridad se verifique en cada etapa del proceso y no solo al
final.

El proyecto parte de una aplicación web con vulnerabilidades conocidas,
sobre la cual se construye un pipeline capaz de detectarlas, corregirlas
y dejar evidencia verificable de todo el proceso.

## Características principales

- Pipeline de Integración y Despliegue Continuo (CI/CD) como código.
- Automatización de pruebas unitarias y de seguridad.
- Integración de herramientas de seguridad (análisis estático, análisis
  de dependencias y análisis dinámico).
- Gestión y actualización automática de dependencias.
- Monitorización de la aplicación en tiempo real.
- Generación automática de documentación y evidencia de cada ejecución.

## Tecnologías utilizadas

- Python
- Flask
- Docker
- Jenkins
- GitHub
- OWASP ZAP
- OWASP Dependency-Check
- Bandit
- Pytest
- Prometheus
- Grafana

## Estructura del proyecto

```
.
├── .github/
├── Jenkinsfile
├── Dockerfile
├── docker-compose.yml
├── docker-compose-grafana.yml
├── prometheus.yml
├── requirements.txt
├── vulnerable_app.py
├── README.md
├── DEPENDENCY_MANAGEMENT.md
└── SDLC_SECURITY_DOCUMENTATION.md
```

## Enfoque general

El proyecto sigue un flujo típico de DevSecOps, donde la seguridad se
incorpora como parte natural del pipeline y no como una revisión
separada:

- Cada cambio en el repositorio dispara automáticamente el pipeline de
  CI/CD.
- La aplicación se construye, se prueba y se despliega en un entorno
  controlado.
- Antes de considerarse lista, pasa por controles de seguridad
  automatizados que revisan tanto el código como sus dependencias y su
  comportamiento en ejecución.
- Una vez desplegada, queda bajo monitorización continua.
- Todo el proceso queda documentado y versionado, de forma que sea
  posible revisar en cualquier momento qué se hizo, cuándo y con qué
  resultado.

## Documentación

El proyecto incluye la siguiente documentación:

- **README.md:** descripción general del proyecto.
- **SDLC_SECURITY_DOCUMENTATION.md:** documentación del proceso de
  seguridad, trazabilidad y actividades realizadas durante el SDLC.
- **DEPENDENCY_MANAGEMENT.md:** gestión de dependencias y actualizaciones
  de seguridad.

## Objetivo

Demostrar la aplicación de prácticas de DevSecOps mediante la integración
de herramientas y procesos que permitan mejorar la seguridad, automatizar
las validaciones y mantener la trazabilidad durante el desarrollo de
software.
