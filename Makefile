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
	rm -fr .coverage*
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
	black aea benchmark examples packages scripts tests
	flake8 aea benchmark examples packages scripts tests

.PHONY: security
security:
	bandit -s B101 -r aea benchmark examples packages scripts tests
	safety check -i 37524 -i 38038 -i 37776 -i 38039

.PHONY: static
static:
	mypy aea benchmark examples packages scripts tests

.PHONY: misc_checks
misc_checks:
	# pip install '.[all]'
	# python scripts/freeze_dependencies.py -o requirements.txt
	# liccheck -s strategy.ini -r requirements.txt -l PARANOID
	# rm -fr requirements.txt
	python scripts/check_copyright_notice.py
	python scripts/generate_ipfs_hashes.py --check

.PHONY: docs
docs:
	mkdocs build --clean

.PHONY: common_checks
common_checks: security misc_checks lint static docs

.PHONY: test
test:
	pytest --doctest-modules aea packages/fetchai/protocols packages/fetchai/connections tests/ --cov-report=html --cov-report=xml --cov-report=term --cov=aea --cov=packages/fetchai/protocols --cov=packages/fetchai/connections
	rm -fr .coverage*

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

h := $(shell git rev-parse --abbrev-ref HEAD)

.PHONY: release_check
release:
	if [ "$h" = "master" ];\
	then\
		echo "Please ensure everything is merged into master & tagged there";\
		pip install twine;\
		twine upload dist/*;\
	else\
		echo "Please change to master branch for release.";\
	fi

v := $(shell pip -V | grep -r virtualenvs)

.PHONY: new_env
new_env: clean
	if [ "$v" == "" ];\
	then\
		pipenv --rm;\
		pipenv --python 3.7;\
		echo "Enter clean virtual environment now: 'pipenv shell'.";\
	else\
		echo "In a virtual environment! Exit first: 'exit'.";\
	fi

.PHONY: install_env
install_env:
	pipenv install --dev --skip-lock
	pip install -e .[all]
