AEA_SRC_DIR := aea
BENCHMARK_DIR := benchmark
EXAMPLES_DIR := examples
PACKAGES_DIR := packages
PLUGINS_DIR := plugins
SCRIPTS_DIR := scripts
AEA_TESTS_DIR := tests

CONNECTIONS_DIR := packages/fetchai/connections
CONTRACTS_DIR := packages/fetchai/contracts
PROTOCOLS_DIR := packages/fetchai/protocols
SKILLS_DIR := packages/fetchai/skills

PLUGIN_FETCHAI_SRC := plugins/aea-ledger-fetchai/aea_ledger_fetchai
PLUGIN_ETHEREUM_SRC := plugins/aea-ledger-ethereum/aea_ledger_ethereum
PLUGIN_COSMOS_SRC := plugins/aea-ledger-cosmos/aea_ledger_cosmos
PLUGIN_CLI_IPFS_SRC := plugins/aea-cli-ipfs/aea_cli_ipfs
PLUGINS_SRC := $(PLUGIN_FETCHAI_SRC) $(PLUGIN_ETHEREUM_SRC) $(PLUGIN_COSMOS_SRC) $(PLUGIN_CLI_IPFS_SRC)

PLUGIN_FETCHAI_TESTS := plugins/aea-ledger-fetchai/tests
PLUGIN_ETHEREUM_TESTS := plugins/aea-ledger-ethereum/tests
PLUGIN_COSMOS_TESTS := plugins/aea-ledger-cosmos/tests
PLUGIN_CLI_IPFS_TESTS := plugins/aea-cli-ipfs/tests
PLUGINS_TESTS := $(PLUGIN_FETCHAI_TESTS) $(PLUGIN_ETHEREUM_TESTS) $(PLUGIN_COSMOS_TESTS) $(PLUGIN_CLI_IPFS_TESTS)

PLUGIN_FETCHAI := plugins/aea-ledger-fetchai
PLUGIN_ETHEREUM := plugins/aea-ledger-ethereum
PLUGIN_COSMOS := plugins/aea-ledger-cosmos
PLUGIN_CLI_IPFS := plugins/aea-cli-ipfs

PYTHON_CODE_DIRS := $(AEA_SRC_DIR) $(BENCHMARK_DIR) $(EXAMPLES_DIR) $(PACKAGES_DIR) $(PLUGINS_DIR) $(SCRIPTS_DIR) $(AEA_TESTS_DIR)

########################################
### Initialise dev environment
########################################

# Create a new poetry virtual environment with all the necessary dependencies installed.
# Once finished, `poetry shell` to enter the virtual environment
v := $(shell pip -V | grep virtualenvs)

.PHONY: new_env
new_env: clean
	if [ -z "$v" ];\
	then\
		poetry install --with dev,docs,packages,tools,testing,types;\
		poetry run pip install --no-deps file:plugins/aea-ledger-ethereum;\
		poetry run pip install --no-deps file:plugins/aea-ledger-cosmos;\
		poetry run pip install --no-deps file:plugins/aea-ledger-fetchai;\
		poetry run pip install --no-deps file:plugins/aea-cli-ipfs;\
		echo "Enter virtual environment with all development dependencies now: 'poetry shell'.";\
	else\
		echo "In a virtual environment! Exit first: 'exit'.";\
	fi

########################################
### Useful linting command
########################################

# Automatically runs black and isort to format the code, and runs flake8 and vulture checks
.PHONY: lint
lint: black isort flake8 vulture

########################################
### Tests
########################################

# Run all tests
.PHONY: test
test:
	pytest -rfE $(PLUGIN_FETCHAI_TESTS)  --cov=aea_ledger_fetchai  --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE $(PLUGIN_ETHEREUM_TESTS) --cov=aea_ledger_ethereum --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE $(PLUGIN_COSMOS_TESTS)   --cov=aea_ledger_cosmos   --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE $(PLUGIN_CLI_IPFS_TESTS) --cov=aea_cli_ipfs        --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE --doctest-modules $(AEA_TESTS_DIR) --cov=$(AEA_SRC_DIR) --cov=$(CONNECTIONS_DIR) --cov=$(CONTRACTS_DIR) --cov=$(PROTOCOLS_DIR) --cov=$(SKILLS_DIR) --cov-report=html --cov-report=term-missing --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

# Run tests for a particular python package
.PHONY: test-sub
test-sub:
	pytest -rfE --doctest-modules $(AEA_TESTS_DIR)/test_$(tdir) --cov=aea.$(dir) --cov-report=html --cov-report=term-missing --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

# Run tests for a particular aea package
.PHONY: test-sub-p
test-sub-p:
	pytest -rfE --doctest-modules $(AEA_TESTS_DIR)/test_packages/test_$(tdir) --cov=packages.fetchai.$(dir) --cov-report=html --cov-report=term-missing --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

# Produce the coverage report. Can see a report summary on the terminal.
# Detailed report on all modules are placed under /coverage-report
.PHONY: coverage-report
coverage-report:
	coverage report -m -i
	coverage html

########################################
### Automatic Styling
########################################

# Automatically formats the code
.PHONY: black
black:
	black $(PYTHON_CODE_DIRS)

# Automatically sorts the imports
.PHONY: isort
isort:
	isort $(PYTHON_CODE_DIRS)

########################################
### Code style checks
########################################

# Runs the black format checker
.PHONY: black-check
black-check:
	black --check --verbose $(PYTHON_CODE_DIRS)

# Runs the isort format checker
.PHONY: isort-check
isort-check:
	isort --check-only --verbose $(PYTHON_CODE_DIRS)

# Runs flake8 checker
.PHONY: flake8
flake:
	flake8 $(PYTHON_CODE_DIRS)

# Runs vulture checker (checks for unused code)
.PHONY: vulture
vulture:
	vulture $(AEA_SRC_DIR) scripts/whitelist.py --exclude '*_pb2.py'

########################################
### Security & safety checks
########################################

# Run both bandit and safety
.PHONY: security
security: bandit safety

# Checks the security of the code
.PHONY: bandit
bandit:
	bandit -r $(AEA_SRC_DIR) $(BENCHMARK_DIR) $(EXAMPLES_DIR) $(PACKAGES_DIR) $(PLUGIN_FETCHAI_SRC) $(PLUGIN_ETHEREUM_SRC) $(PLUGIN_COSMOS_SRC) $(PLUGIN_CLI_IPFS_SRC)
	bandit -s B101 -r $(AEA_TESTS_DIR) $(SCRIPTS_DIR)

# Checks the security of the code
.PHONY: safety
safety:
	safety check -i 44610 -i 50473

########################################
### Linters
########################################

# Runs the mypy linter
.PHONY: mypy
mypy:
	mypy aea packages benchmark --disallow-untyped-defs
	mypy examples --check-untyped-defs
	mypy scripts
	mypy tests --exclude "serialization.py"

# Runs the pylint linter
.PHONY: pylint
pylint:
	pylint -j0 -d E1136 $(AEA_SRC_DIR) $(BENCHMARK_DIR) $(EXAMPLES_DIR) $(PACKAGES_DIR) $(SCRIPTS_DIR) $(PLUGIN_FETCHAI_SRC) $(PLUGIN_ETHEREUM_SRC) $(PLUGIN_COSMOS_SRC) $(PLUGIN_CLI_IPFS_SRC)

########################################
### License and copyright checks
########################################

# Check licenses
.PHONY: liccheck
liccheck:
	poetry export > tmp-requirements.txt
	liccheck -s strategy.ini -r tmp-requirements.txt -l PARANOID
	rm -frv tmp-requirements.txt

# Check copyrights
.PHONY: copyright-check
copyright-check:
	python scripts/check_copyright.py

########################################
### Docs
########################################

# Build documentation
.PHONY: docs
docs:
	mkdocs build --clean

# Live documentation server
.PHONY: docs-live
docs-live:
	mkdocs serve

# Generate API documentation (ensure you add the new pages created into /mkdocs.yml --> nav)
.PHONY: generate-api-docs
generate-api-docs:
	python scripts/generate_api_docs.py

########################################
### Update Poetry Lock
########################################

# Updates the poetry lock
poetry.lock: pyproject.toml
	poetry lock

########################################
### Clear the caches and temporary files
########################################

# clean the caches and temporary files and directories
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
	rm -rf plugins/*/build
	rm -rf plugins/*/dist

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

########################################
### Package checks
########################################

# Run package checks (validate the hashes, correct version in the docs, etc)
.PHONY: package_checks
package_checks:
	python scripts/generate_ipfs_hashes.py --check
	python scripts/check_package_versions_in_docs.py
	python scripts/check_packages.py

########################################
### Build
########################################

.PHONY: dist
dist: clean
	poetry build

protolint_install:
	GO111MODULE=on GOPATH=~/go go install github.com/yoheimuta/protolint/cmd/protolint@v0.27.0
protolint:
	PATH=${PATH}:${GOPATH}/bin/:~/go/bin protolint lint -config_path=./protolint.yaml -fix ./aea/mail ./packages/fetchai/protocols
protolint_install_win:
	powershell -command '$$env:GO111MODULE="on"; go install github.com/yoheimuta/protolint/cmd/protolint@v0.27.0'
protolint_win:
	protolint lint -config_path=./protolint.yaml -fix ./aea/mail ./packages/fetchai/protocols
