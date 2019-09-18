
pipeline {

    agent none
        //
        // pip install tox pipenv

    stages {

        stage('Unit Tests & Code Style Check') {

            parallel {

                stage('Code Style Check') {

                    steps {
                        sh 'pip3 install tox'
                        sh 'tox -e flake8'
                    }

                } // code style check

                stage('Static Type Check') {

                    steps {
                        sh 'pip3 install mypy'
                        sh 'mypy aea tests examples'
                    }

                } // static type check

                stage('Unit Tests: Python 3.6') {

                    agent {
                        docker {
                            image "python:3.6-alpine"
                        }
                    }

                    steps {
                        sh 'apk add --no-cache openssl-dev libffi-dev gcc musl-dev'
                        sh 'pip install tox pipenv'
                        sh 'tox -e py36'
                    }

                }  // unit tests: python 3.6

                stage('Unit Tests: Python 3.7') {

                    agent {
                        docker {
                            image "python:3.7-alpine"
                        }
                    }

                    steps {
                        sh 'apk add --no-cache openssl-dev libffi-dev gcc musl-dev'
                        sh 'pip install tox pipenv'
                        sh 'tox -e py37'
                    }

                } // unit tests: python 3.7

            } // parallel

        }  // unit tests & code style check

    } // stages

} // pipeline
