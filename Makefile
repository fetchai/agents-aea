AEA_SRC_DIR := aea
BENCHMARK_DIR := benchmark
EXAMPLES_DIR := examples
LIBS_DIR := libs
PACKAGES_DIR := packages
PLUGINS_DIR := plugins
SCRIPTS_DIR := scripts
AEA_TESTS_DIR := tests
AEA_CORE_TESTS_DIRS := tests/test_aea tests/test_aea_extra ./tests/test_docs
EXAMPLES_TESTS_DIRS := tests/test_examples
PACKAGES_TESTS_DIRS := packages/fetchai/protocols packages/fetchai/connections packages/fetchai/skills ./tests/test_packages ./tests/test_packages_for_aea_tests ./tests/test_aea_core_packages
DOCS_TESTS_DIR := tests/test_docs
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

.PHONY: new-env
new-env: clean
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
### Tests
########################################

# Run all tests
.PHONY: test
test: test-aea-all test-plugins

# Run all aea tests
.PHONY: test-aea-all
test-aea-all:
	pytest -rfE --doctest-modules $(AEA_TESTS_DIR) --cov=$(AEA_SRC_DIR) --cov=$(CONNECTIONS_DIR) --cov=$(CONTRACTS_DIR) --cov=$(PROTOCOLS_DIR) --cov=$(SKILLS_DIR) --cov-report=html --cov-report=term-missing
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: test-aea-core
test-aea-core:
	pytest -rfE --doctest-modules $(AEA_CORE_TESTS_DIRS) --cov=$(AEA_SRC_DIR) --cov-report=html --cov-report=term-missing
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: test-packages
test-packages:
	pytest -rfE --cov=packages/fetchai/connections --cov=packages/fetchai/contracts --cov=packages/fetchai/protocols --cov=packages/fetchai/skills --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term --cov=aea --cov=packages/fetchai/protocols --cov=packages/fetchai/connections --cov=packages/fetchai/skills $(PACKAGES_TESTS_DIRS)
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: test-docs
test-docs:
	pytest -rfE --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term --cov=aea $(DOCS_TESTS_DIR)
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;


.PHONY: test-examples
test-examples:
	pytest -rfE --cov=packages/fetchai/connections --cov=packages/fetchai/contracts --cov=packages/fetchai/protocols --cov=packages/fetchai/skills --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term --cov=aea --cov=packages/fetchai/protocols --cov=packages/fetchai/connections --cov=packages/fetchai/skills $(EXAMPLES_TESTS_DIRS)
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;


# Run all plugin tests
.PHONY: test-plugins
test-plugins:
	pytest -rfE $(PLUGIN_FETCHAI_TESTS)  --cov=aea_ledger_fetchai  --cov-report=term-missing
	pytest -rfE $(PLUGIN_ETHEREUM_TESTS) --cov=aea_ledger_ethereum --cov-report=term-missing
	pytest -rfE $(PLUGIN_COSMOS_TESTS)   --cov=aea_ledger_cosmos   --cov-report=term-missing
	pytest -rfE $(PLUGIN_CLI_IPFS_TESTS) --cov=aea_cli_ipfs        --cov-report=term-missing
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

# Run tests for a particular python package
.PHONY: test-sub
test-sub:
	pytest -rfE --doctest-modules $(AEA_TESTS_DIR)/test_$(tdir) --cov=aea.$(dir) --cov-report=html --cov-report=term-missing
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

# Run tests for a particular aea package
.PHONY: test-sub-p
test-sub-p:
	pytest -rfE --doctest-modules $(AEA_TESTS_DIR)/test_packages/test_$(tdir) --cov=packages.fetchai.$(dir) --cov-report=html --cov-report=term-missing
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

# Produce the coverage report. Can see a report summary on the terminal.
# Detailed report on all modules are placed under /htmlcov
.PHONY: coverage-report
coverage-report:
	coverage report -m -i
	coverage html

########################################
### Code Styling
########################################

# Automatically run black and isort to format the code, and run flake8 and vulture checks
.PHONY: lint
lint: black isort flake8 vulture

# Automatically format the code using black
.PHONY: black
black:
	black $(PYTHON_CODE_DIRS)

# Automatically sort the imports
.PHONY: isort
isort:
	isort $(PYTHON_CODE_DIRS)

# Check the code format
.PHONY: black-check
black-check:
	black --check --verbose $(PYTHON_CODE_DIRS)

# Check the imports are sorted
.PHONY: isort-check
isort-check:
	isort --check-only --verbose $(PYTHON_CODE_DIRS)

# Run flake8 linter
.PHONY: flake8
flake8:
	flake8 $(PYTHON_CODE_DIRS)

# Check for unused code
.PHONY: vulture
vulture:
	vulture $(AEA_SRC_DIR) scripts/whitelist.py --exclude '*_pb2.py'

########################################
### Security & safety checks
########################################

# Run bandit and safety
.PHONY: security
security: bandit safety

# Check the security of the code
.PHONY: bandit
bandit:
	bandit -r $(AEA_SRC_DIR) $(BENCHMARK_DIR) $(EXAMPLES_DIR) $(PACKAGES_DIR) $(PLUGIN_FETCHAI_SRC) $(PLUGIN_ETHEREUM_SRC) $(PLUGIN_COSMOS_SRC) $(PLUGIN_CLI_IPFS_SRC)
	bandit -s B101 -r $(AEA_TESTS_DIR) $(SCRIPTS_DIR)

# Check the security of the code for known vulnerabilities
.PHONY: safety
safety:
	safety check -i 44610 -i 50473

########################################
### Linters
########################################

# Check types (statically) using mypy
.PHONY: mypy
mypy:
	mypy aea packages benchmark --disallow-untyped-defs
	mypy examples --check-untyped-defs
	mypy scripts
	mypy tests --exclude "serialization.py"

# Lint the code using pylint
.PHONY: pylint
pylint:
	pylint -j0 -d E1136 $(AEA_SRC_DIR) $(BENCHMARK_DIR) $(EXAMPLES_DIR) $(PACKAGES_DIR) $(SCRIPTS_DIR) $(PLUGIN_FETCHAI_SRC) $(PLUGIN_ETHEREUM_SRC) $(PLUGIN_COSMOS_SRC) $(PLUGIN_CLI_IPFS_SRC)

########################################
### License and copyright checks
########################################

# Check dependency licenses
.PHONY: liccheck
liccheck:
	poetry export > tmp-requirements.txt
	liccheck -s strategy.ini -r tmp-requirements.txt -l PARANOID
	rm -frv tmp-requirements.txt

# Check that the relevant files have appropriate Copyright header
.PHONY: copyright-check
copyright-check:
	python scripts/check_copyright_notice.py --directory .

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
	python scripts/generate_api_docs.py $(args)

# Check links are live in the documentation
.PHONY: check-doc-links
check-doc-links:
	python scripts/check_doc_links.py

########################################
### Poetry Lock
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
### Packages
########################################

# Update package hashes
.PHONY: update-package-hashes
update-package-hashes:
	python scripts/generate_ipfs_hashes.py

# Run all package checks
.PHONY: package-checks
package-checks: check-package-hashes check-package-versions-in-docs check-packages

# Check package hashes
.PHONY: check-package-hashes
check-package-hashes:
	python scripts/generate_ipfs_hashes.py --check

# Check correct package version in the docs
.PHONY: check-package-versions-in-docs
check-package-versions-in-docs:
	python scripts/check_package_versions_in_docs.py

# Perform various checks on packages
.PHONY: check-packages
check-packages:
	python scripts/check_packages.py

########################################
### Other checks
########################################

# Check that libp2p code in libs and connection aren't different
.PHONY: libp2p-diffs
libp2p-diffs:
	diff libs/go/libp2p_node packages/fetchai/connections/p2p_libp2p/libp2p_node -r

# Check that plugins for Cosmos and Fetch.ai, and Plugins' and main Licenses aren't different
.PHONY: plugin-diffs
plugin-diffs:
	diff $(PLUGIN_COSMOS_SRC)/cosmos.py $(PLUGIN_FETCHAI_SRC)/_cosmos.py
	diff LICENSE $(PLUGIN_COSMOS)/LICENSE
	diff LICENSE $(PLUGIN_ETHEREUM)/LICENSE
	diff LICENSE $(PLUGIN_FETCHAI)/LICENSE

########################################
### Build
########################################

# Build the project
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
