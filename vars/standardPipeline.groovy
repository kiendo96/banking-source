def call(Map config) {
    // Tự động lấy Agent dựa trên yêu cầu của Service, mặc định là python, kaniko, git
    // Bạn có thể truyền config.tools từ Jenkinsfile của từng service
    def myAgentYaml = agentFactory(tools: config.tools ?: ['python', 'kaniko', 'git'])

    pipeline {
        agent {
            kubernetes {
                yaml myAgentYaml
            }
        }
        environment {
            DOCKER_REGISTRY = 'harbor.local/banking-demo'
            IMAGE_NAME = "${config.serviceName}"
            IMAGE_TAG = "${env.BUILD_NUMBER}"
            GITOPS_REPO = 'https://github.com/kiendo96/banking-gitops.git'
        }
        stages {
            stage('Docker Build & Push') {
                steps {
                    container('kaniko') {
                        script {
                            echo "Building image: ${IMAGE_NAME}:${IMAGE_TAG}"
                            
                            withCredentials([usernamePassword(credentialsId: 'harbor-credentials', passwordVariable: 'HARBOR_PSW', usernameVariable: 'HARBOR_USR')]) {
                                sh """
                                    mkdir -p /kaniko/.docker
                                    echo '{"auths":{"harbor.local":{"username":"${HARBOR_USR}","password":"${HARBOR_PSW}"}}}' > /kaniko/.docker/config.json
                                """
                            }
                            
                            sh "/kaniko/executor --context `pwd` --dockerfile ${config.dockerfilePath} --destination ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} --insecure --skip-tls-verify"
                        }
                    }
                }
            }
            stage('Update GitOps Tag') {
                steps {
                    container('git') {
                        script {
                            echo "Updating GitOps repository with new image tag..."
                            sh "rm -rf banking-gitops-tmp && git clone ${GITOPS_REPO} banking-gitops-tmp"
                            
                            dir('banking-gitops-tmp') {
                                sh "git config user.email 'jenkins@banking.local'"
                                sh "git config user.name 'Jenkins CI'"
                                
                                def valuesFile = "apps/${config.serviceName}/helm/values-dev.yaml"
                                sh "sed -i 's/tag: .*/tag: \"${IMAGE_TAG}\"/' ${valuesFile}"
                                
                                sh "git add ${valuesFile}"
                                sh "git commit -m 'chore: update ${config.serviceName} image tag to ${IMAGE_TAG}'"
                                
                                withCredentials([usernamePassword(credentialsId: 'github-credentials', passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                                    sh "git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/kiendo96/banking-gitops.git main"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}