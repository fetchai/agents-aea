
pipeline {

    agent {

        docker 'gcr.io/organic-storm-201412/aea-develop:latest'

    }

    options {
        timeout(time: 2, unit: 'HOURS')
    }

    stages {

        stage('Unit Tests & Code Style Check') {

            parallel {

                stage('Security Check: Main') {

                    steps {
                        sh 'tox -e bandit-main'
                    }

                } // bandit security check main

                stage('Security Check: Tests') {

                    steps {
                        sh 'tox -e bandit-tests'
                    }

                } // bandit security check tests

                stage('Black Reformatting') {

                    steps {
                        sh 'tox -e black-check'
                    }

                } // black reformatting check

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

                // stage('Docs') {

                //     steps {
                //         sh 'tox -e docs'
                //     }

                // } // docs

                stage('Unit Tests: Python 3.6') {

                    steps {
                        sh 'tox -e py36 -- --no-integration-tests --ci'
                    }

                }  // unit tests: python 3.6

                stage('Unit Tests: Python 3.7') {

                    steps {
                        sh 'tox -e py37 -- --no-integration-tests --ci'
                    }

                } // unit tests: python 3.7

                stage('Unit Tests: Python 3.8') {

                    steps {
                        sh 'tox -e py38 -- --no-integration-tests --ci'
                    }

                } // unit tests: python 3.8

            } // parallel

        }  // unit tests & code style check

    } // stages

} // pipeline
