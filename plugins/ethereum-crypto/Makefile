.PHONY: clean
clean: clean-build clean-pyc clean-test clean-docs

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr pip-wheel-metadata
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +
	rm -fr Pipfile.lock

.PHONY: clean-docs
clean-docs:
	rm -fr site/

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.DS_Store' -exec rm -fr {} +

.PHONY: clean-test
clean-test:
	rm -fr .tox/
	rm -f .coverage
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;
	rm -fr coverage.xml
	rm -fr htmlcov/
	rm -fr .hypothesis
	rm -fr .pytest_cache
	rm -fr .mypy_cache/
	rm -fr input_file
	rm -fr output_file
	find . -name 'log.txt' -exec rm -fr {} +
	find . -name 'log.*.txt' -exec rm -fr {} +

.PHONY: lint
lint:
	black ethereum_crypto tests
	isort ethereum_crypto tests
	flake8 ethereum_crypto tests
	vulture ethereum_crypto scripts/whitelist.py

.PHONY: pylint
pylint:
	pylint ethereum_crypto

.PHONY: security
security:
	bandit -r ethereum_crypto tests
	bandit -s B101 -r tests scripts
	safety check -i 37524 -i 38038 -i 37776 -i 38039

.PHONY: static
static:
	mypy ethereum_crypto tests

.PHONY: common_checks
common_checks: security lint static

.PHONY: test
test:
	pytest -rfE --doctest-modules ethereum_crypto tests/ --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term  --cov=ethereum_crypto --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;


.PHONY: test-all
test-all:
	tox

.PHONY: install
install: clean
	python3 setup.py install

.PHONY: dist
dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
