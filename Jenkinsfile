
pipeline {

    agent {

        docker 'gcr.io/organic-storm-201412/aea-develop:latest'

    }

    options {
        timeout(time: 1, unit: 'HOURS')
    }

    stages {

        stage('Code Style & Other Checks') {

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

                stage('Safety Check') {

                    steps {
                        sh 'tox -e safety'
                    }

                } // safety check

                stage('License Check') {

                    steps {
                        sh 'tox -e liccheck'
                    }

                } // license check

                stage('Copyright Check') {

                    steps {
                        sh 'tox -e copyright_check'
                    }

                } // copyright check

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

                stage('Docs') {

                    steps {
                        sh 'tox -e docs'
                    }
                } // docs

            }
        } // code style and other checks

        stage('Unit Tests: py37') {

            parallel {

                stage('Unit Tests: Python 3.7') {

                    steps {
                        sh 'tox -e py37 -- --no-integration-tests --ci'
                    }

                }  // unit tests: python 3.7

            }

        } // unit tests py37

        stage('Unit Tests: py36, py38') {

            parallel {

                stage('Unit Tests: Python 3.6') {

                    steps {
                        sh 'tox -e py36 -- --no-integration-tests --ci'
                    }

                } // unit tests: python 3.6

                stage('Unit Tests: Python 3.8') {

                    steps {
                        sh 'tox -e py38 -- --no-integration-tests --ci'
                    }

                } // unit tests: python 3.8

            } // parallel

        }  // unit tests py36, py38

    } // stages

} // pipeline
