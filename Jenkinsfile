pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    // Requires the GitHub plugin and a webhook pointing to /github-webhook/.
    triggers {
        githubPush()
    }

    environment {
        LOCAL_IMAGE = "counter-app:${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Unit tests') {
            steps {
                sh '''
                    set -eu
                    python3 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install --disable-pip-version-check -r requirements-dev.txt
                    mkdir -p reports
                    python -m pytest -q --junitxml=reports/pytest.xml
                '''
            }
        }

        stage('Build Docker image') {
            when {
                branch 'main'
            }
            steps {
                sh 'docker build -t "$LOCAL_IMAGE" .'
            }
        }

        stage('Publish to Docker Hub') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKERHUB_USER',
                    passwordVariable: 'DOCKERHUB_TOKEN'
                )]) {
                    sh '''
                        set +x
                        echo "$DOCKERHUB_TOKEN" | docker login \
                            --username "$DOCKERHUB_USER" --password-stdin
                        docker tag "$LOCAL_IMAGE" "$DOCKERHUB_USER/counter-app:$BUILD_NUMBER"
                        docker tag "$LOCAL_IMAGE" "$DOCKERHUB_USER/counter-app:latest"
                        docker push "$DOCKERHUB_USER/counter-app:$BUILD_NUMBER"
                        docker push "$DOCKERHUB_USER/counter-app:latest"
                        docker logout
                    '''
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/pytest.xml'
        }
    }
}
