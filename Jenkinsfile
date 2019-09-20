
pipeline {

    agent {

        docker 'gcr.io/organic-storm-201412/aea-develop:latest'

    }

    stages {

        stage('Unit Tests & Code Style Check') {

            parallel {

                stage('Code Style Check') {

                    steps {
                        sh 'tox -e flake8'
                    }

                } // code style check

                stage('Static Type Check') {

                    steps {
                        sh 'tox -e mypy'
                    }

                } // static type check

                stage('Docs') {

                    steps {
                        sh 'tox -e docs'
                    }

                } // docs

                stage('Unit Tests: Python 3.6') {

                    steps {
                        sh 'tox -e py36 -- --no-integration-tests'
                    }

                }  // unit tests: python 3.6

                stage('Unit Tests: Python 3.7') {

                    steps {
                        sh 'tox -e py37 -- --no-integration-tests'
                    }

                } // unit tests: python 3.7

            } // parallel

        }  // unit tests & code style check

    } // stages

} // pipeline
