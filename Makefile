clean: clean-build clean-pyc clean-test clean-docs

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-docs:
	rm -fr site/

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr .coverage*
	rm -fr htmlcov/
	rm -fr .hypothesis
	rm -fr .pytest_cache
	rm -fr .mypy_cache/
	rm -fr input_file
	rm -fr output_file
	find . -name 'log.txt' -exec rm -fr {} +
	find . -name 'log.*.txt' -exec rm -fr {} +

lint:
	black aea examples packages scripts tests
	flake8 aea examples packages scripts tests

security:
	bandit -s B101 -r aea packages scripts
	bandit -s B101 -r tests
	safety check

static:
	mypy aea packages tests scripts

test:
	pytest --doctest-modules aea packages/fetchai/protocols packages/fetchai/connections tests/ --cov-report=html --cov-report=xml --cov-report=term --cov=aea --cov=packages/fetchai/protocols --cov=packages/fetchai/connections
	rm -fr .coverage*

test-all:
	tox

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean
	python3 setup.py install