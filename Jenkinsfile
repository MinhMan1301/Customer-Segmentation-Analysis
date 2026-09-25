// Customer Segmentation Analysis - Jenkins declarative pipeline (SIT223/SIT753 Task 7.3HD)
//
// Build -> Test -> Code Quality -> Security -> Deploy (staging) -> Release (production) -> Monitoring
//
// The Jenkinsfile only orchestrates; the logic of every stage lives in ci/*.sh so it can be
// run and debugged locally with exactly the same commands. See docs/PIPELINE.md.

pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
        timeout(time: 90, unit: 'MINUTES')
    }

    // Local Jenkins cannot receive GitHub webhooks, so it polls GitHub every ~2 minutes:
    // every push to the repository triggers a build automatically.
    triggers {
        pollSCM('H/2 * * * *')
    }

    parameters {
        booleanParam(name: 'RELEASE_TO_PRODUCTION', defaultValue: true,
                     description: 'Promote the verified build to production and publish a GitHub Release (main branch only).')
        booleanParam(name: 'SIMULATE_INCIDENT', defaultValue: false,
                     description: 'After release, stop production to prove that the CSAppDown alert fires and resolves.')
    }

    environment {
        GITHUB_REPO      = 'MinhMan1301/Customer-Segmentation-Analysis'   // <owner>/<repo>
        NOTIFY_TO        = 'phamminhman1312005@gmail.com'                     // pipeline + alert e-mails
        REGISTRY         = 'localhost:5000'
        APP_NAME         = 'cs-app'
        DATASET_TAG      = 'dataset-v1'
        DATASET_ROOT     = '/datasets'
        DEPLOY_STATE_DIR = '/var/jenkins_home/deploy-state'
    }

    stages {
        stage('Build') {
            steps {
                sh 'rm -rf reports && mkdir -p reports'
                script {
                    env.GIT_SHA = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                    env.APP_VERSION = "${readFile('VERSION').trim()}.${env.BUILD_NUMBER}"
                    currentBuild.displayName = "#${env.BUILD_NUMBER} v${env.APP_VERSION}"
                    currentBuild.description = "commit ${env.GIT_SHA.substring(0, 7)}"
                }
                sh 'bash ci/build.sh'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'reports/build-info.json', fingerprint: true
                }
            }
        }

        stage('Test') {
            steps {
                sh 'bash ci/test.sh'      // unit + integration, coverage gate 80%
                sh 'bash ci/smoke.sh'     // run the built image once: health, /metrics version, pipeline
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                    recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']],
                                   sourceDirectories: [[path: 'src']])
                    publishHTML(target: [reportName: 'Coverage report', reportDir: 'reports/coverage-html',
                                         reportFiles: 'index.html', keepAll: true, alwaysLinkToLastBuild: true,
                                         allowMissing: true])
                }
            }
        }

        stage('Code Quality') {
            environment {
                SCANNER_HOME = tool 'SonarScanner'
            }
            steps {
                sh 'bash ci/quality.sh'   // flake8, hadolint (Dockerfiles), shellcheck (CI scripts)
                withSonarQubeEnv('SonarQube') {
                    sh '"$SCANNER_HOME/bin/sonar-scanner" -Dsonar.projectVersion="$APP_VERSION"'
                }
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true   // "CS Gate": coverage, duplication, ratings
                }
            }
            post {
                always {
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/flake8.txt, reports/hadolint.txt, reports/shellcheck.txt'
                }
            }
        }

        stage('Security') {
            parallel {
                stage('SAST - Bandit') {
                    steps { sh 'bash ci/security.sh bandit' }
                }
                stage('Dependencies - pip-audit') {
                    steps { sh 'bash ci/security.sh pip-audit' }
                }
                stage('Image, SBOM, secrets - Trivy') {
                    steps { sh 'bash ci/security.sh trivy' }
                }
            }
            post {
                always {
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/security/**'
                    publishHTML(target: [reportName: 'Bandit report', reportDir: 'reports/security',
                                         reportFiles: 'bandit.html', keepAll: true, allowMissing: true,
                                         alwaysLinkToLastBuild: true])
                }
            }
        }

        stage('Deploy') {   // test environment: staging (sample data)
            steps {
                sh 'bash ci/deploy.sh deploy staging'   // compose up --wait, health + version check, auto-rollback
                sh 'bash ci/e2e.sh staging'             // Selenium browser tests against staging
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/e2e-staging.xml'
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/e2e/staging/*.png'
                }
                failure {
                    sh 'bash ci/deploy.sh rollback staging || true'
                }
            }
        }

        stage('Release') {  // production (full dataset) + tag + GitHub Release
            when {
                allOf {
                    expression { params.RELEASE_TO_PRODUCTION != false }   // null on the very first build
                    expression { (env.GIT_BRANCH ?: 'main') ==~ /(origin\/)?main/ }
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-creds',
                                                  usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                    sh 'bash ci/fetch_dataset.sh'                       // full data from GitHub Release, SHA-256 verified
                    sh 'bash ci/deploy.sh deploy production'
                    sh 'bash ci/e2e.sh production'                     // full dataset: long first load, row-count check
                    sh 'bash ci/release.sh'                             // :stable tag, git tag vX.Y.N, GitHub Release
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/e2e-production.xml'
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/e2e/production/*.png, reports/release.txt'
                }
                failure {
                    sh 'bash ci/deploy.sh rollback production || true'
                }
            }
        }

        stage('Monitoring') {
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'smtp-creds', usernameVariable: 'SMTP_USER', passwordVariable: 'SMTP_PASSWORD'),
                    usernamePassword(credentialsId: 'grafana-admin', usernameVariable: 'GRAFANA_USER', passwordVariable: 'GRAFANA_PASSWORD')
                ]) {
                    sh 'ALERT_EMAIL_TO="$NOTIFY_TO" bash ci/monitoring.sh up'
                    sh 'bash ci/monitoring.sh verify'
                    script {
                        if (params.SIMULATE_INCIDENT == true) {
                            sh 'bash ci/monitoring.sh incident'
                        }
                    }
                }
            }
            post {
                always {
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/monitoring/**'
                }
            }
        }
    }

    post {
        always {
            sh 'docker rm -f "cs-selenium-$BUILD_NUMBER" "cs-ci-smoke-$BUILD_NUMBER" >/dev/null 2>&1 || true'
        }
        success {
            emailext(
                to: "${env.NOTIFY_TO}",
                subject: "SUCCESS: ${env.JOB_NAME} v${env.APP_VERSION}",
                mimeType: 'text/html',
                body: """<p>Build <a href="${env.BUILD_URL}">#${env.BUILD_NUMBER}</a> passed all stages.</p>
                         <ul><li>Version: ${env.APP_VERSION}</li><li>Commit: ${env.GIT_SHA}</li>
                         <li>Staging: http://localhost:8502 &middot; Production: http://localhost:8501</li>
                         <li>Grafana: http://localhost:3000 &middot; Prometheus: http://localhost:9090</li></ul>"""
            )
        }
        failure {
            emailext(
                to: "${env.NOTIFY_TO}",
                subject: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                mimeType: 'text/html',
                attachLog: true,
                body: """<p>Build <a href="${env.BUILD_URL}">#${env.BUILD_NUMBER}</a> failed.
                         Open the console log (attached) and the stage view to find the failing stage.</p>"""
            )
        }
    }
}
