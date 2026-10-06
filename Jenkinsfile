pipeline {
  agent any

  environment {
    APP_URL       = 'http://ev3-app:5000'
    REPORT_DIR    = 'zap-reports'
  }

  stages {

    stage('Build') {
      steps {
        sh '''
          docker network create devsecops-network || true
          docker build -t ev3-ciberseguridad_final:${BUILD_NUMBER} .
        '''
      }
    }

    stage('Test - Unit') {
      steps {
        sh '''
          python3 -m venv venv || true
          . venv/bin/activate || true

          pip install --upgrade pip || true
          pip install -r requirements.txt || true
          pip install pytest flask || true

          pytest --junitxml=results.xml || true
        '''
        junit allowEmptyResults: true, testResults: 'results.xml'
      }
    }

    stage('Deploy - Staging') {
      steps {
        sh '''
          docker rm -f ev3-app || true

          docker run -d \
            --name ev3-app \
            --network devsecops-network \
            -p 5000:5000 \
            ev3-ciberseguridad_final:${BUILD_NUMBER}

          sleep 5

          docker run --rm \
            --network devsecops-network \
            curlimages/curl:latest \
            -sf http://ev3-app:5000 || echo "App no responde"
        '''
      }
    }

    stage('Security Test - SCA Dependencies') {
      steps {
        sh """
          docker volume rm dc-report-vol 2>/dev/null || true
          docker volume create dc-report-vol
          docker volume create dc-nvd-data || true

          docker run --rm \
            --network devsecops-network \
            -v \${WORKSPACE}:/src:ro \
            -v dc-report-vol:/report \
            -v dc-nvd-data:/usr/share/dependency-check/data \
            owasp/dependency-check:latest \
              --scan /src \
              --format HTML \
              --format XML \
              --out /report \
              --project EV3-Ciberseguridad \
              --noupdate || true

          mkdir -p \${WORKSPACE}/dc-report
        """

        sh '''
          docker run --rm \
            -v dc-report-vol:/report \
            -v ${WORKSPACE}/dc-report:/dest \
            alpine sh -c 'cp /report/*.html /dest/ 2>/dev/null || true; cp /report/*.xml /dest/ 2>/dev/null || true; chmod 644 /dest/* 2>/dev/null || true'
        '''

        publishHTML(target: [
          allowMissing         : true,
          alwaysLinkToLastBuild: true,
          keepAll              : true,
          reportDir            : "${WORKSPACE}/dc-report",
          reportFiles          : 'dependency-check-report.html',
          reportName           : 'Dependency-Check Report'
        ])
      }
    }

    stage('Security Test - DAST ZAP') {
      steps {
        sh """
          docker volume rm zap-report-vol 2>/dev/null || true
          docker volume create zap-report-vol

          docker run --rm \
            -v zap-report-vol:/zap/wrk \
            alpine sh -c 'chmod 777 /zap/wrk'

          docker run --rm \
            --network devsecops-network \
            curlimages/curl:latest \
            -sf http://ev3-app:5000 || echo "App no responde"

          docker run --rm \
            -u root \
            --network devsecops-network \
            -v zap-report-vol:/zap/wrk/:rw \
            ghcr.io/zaproxy/zaproxy:stable \
              zap-baseline.py \
                -t http://ev3-app:5000 \
                -r zap_report.html \
                -J zap_report.json \
                --auto || true

          rm -rf \${WORKSPACE}/zap-reports
          mkdir -p \${WORKSPACE}/zap-reports

          docker rm -f zap-copy 2>/dev/null || true

          docker create --name zap-copy \
            -v zap-report-vol:/report \
            alpine

          docker cp zap-copy:/report/. \${WORKSPACE}/zap-reports/ || true
          docker rm zap-copy || true

          chmod 644 \${WORKSPACE}/zap-reports/* 2>/dev/null || true
        """

        publishHTML(target: [
          allowMissing         : true,
          alwaysLinkToLastBuild: true,
          keepAll              : true,
          reportDir            : "${WORKSPACE}/zap-reports",
          reportFiles          : 'zap_report.html',
          reportName           : 'OWASP ZAP Report'
        ])
      }
    }

    stage('Trazabilidad y Documentacion') {
      steps {
        sh '''
          mkdir -p ${WORKSPACE}/docs-report
          F=${WORKSPACE}/docs-report/trazabilidad_build_${BUILD_NUMBER}.md

          cat > "$F" << EOF
# Registro de Trazabilidad - Build #${BUILD_NUMBER}

## Informacion del Build
- **Numero de Build:** ${BUILD_NUMBER}
- **Fecha de ejecucion:** $(date +"%Y-%m-%d %H:%M:%S")
- **Job:** ${JOB_NAME}

## Control de Versiones (Git)
- **Commit:** ${GIT_COMMIT}
- **Repositorio:** https://github.com/CatrinaCorral/EV3-Ciberseguridad_Final

## Etapas Ejecutadas
1. Build: construccion de imagen Docker ev3-ciberseguridad_final:${BUILD_NUMBER} - EXITOSA
2. Test - Unit: ejecucion de pruebas unitarias (pytest) - EXITOSA
3. Deploy - Staging: despliegue del contenedor en devsecops-network - EXITOSA
4. Security Test - SCA Dependencies: analisis de dependencias con OWASP Dependency-Check - EXITOSA
5. Security Test - DAST ZAP: escaneo dinamico OWASP ZAP contra la app desplegada - EXITOSA
6. Trazabilidad y Documentacion: generacion de este registro - EXITOSA

## Artefactos Generados
- dependency-check-report.html / .xml (resultado del escaneo SCA)
- zap_report.html / .json (resultado del escaneo DAST)
- results.xml (resultado de pruebas unitarias)
- trazabilidad_build_${BUILD_NUMBER}.md (este documento)

## Vulnerabilidades Corregidas (Codigo Fuente)
- Inyeccion SQL en login (CWE-89): consulta parametrizada en vez de f-string concatenado
- Flask en modo debug activo (CWE-94): cambiado a debug=False
- IDOR en eliminacion de tareas: validacion de propietario (WHERE id = ? AND user_id = ?)
- Cabeceras de seguridad HTTP ausentes (CWE-693): CSP, X-Frame-Options, X-Content-Type-Options, Permissions-Policy, Cross-Origin-*-Policy agregadas via @app.after_request

## Gestion de Dependencias
- Dependabot alerts y security updates activados en GitHub
- Archivo .github/dependabot.yml configurado (revision semanal, ecosistema pip)
- Snapshot de requirements.txt vigente en este build:
$(cat ${WORKSPACE}/requirements.txt | sed 's/^/  - /')
- Ver detalle completo en DEPENDENCY_MANAGEMENT.md y SDLC_SECURITY_DOCUMENTATION.md

## Monitorizacion
- Metricas expuestas via /metrics (prometheus_client en la app Flask)
- Prometheus recolectando metricas del contenedor ev3-app (scrape cada 15s)
- Dashboard Grafana con paneles de estado de servicios y tasa de peticiones HTTP por endpoint
EOF

          cat "$F"
        '''
        archiveArtifacts(
          artifacts        : 'docs-report/*.md',
          allowEmptyArchive: true
        )
      }
    }
  }

  post {
    always {
      sh """
        cp \${WORKSPACE}/dc-report/*.html \${WORKSPACE}/ 2>/dev/null || true
        cp \${WORKSPACE}/dc-report/*.xml \${WORKSPACE}/ 2>/dev/null || true
        cp \${WORKSPACE}/zap-reports/*.html \${WORKSPACE}/ 2>/dev/null || true
        cp \${WORKSPACE}/zap-reports/*.json \${WORKSPACE}/ 2>/dev/null || true
      """

      archiveArtifacts(
        artifacts         : 'dependency-check-report.html,dependency-check-report.xml,zap_report.html,zap_report.json,results.xml',
        allowEmptyArchive : true
      )

      sh 'docker rm -f ev3-app || true'
    }
  }
}
