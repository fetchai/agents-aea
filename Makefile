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

.PHONY: lint
lint:
	black aea benchmark examples packages plugins scripts tests
	isort aea benchmark examples packages plugins scripts tests
	flake8 aea benchmark examples packages plugins scripts tests
	vulture aea scripts/whitelist.py --exclude "*_pb2.py"
	darglint aea benchmark examples libs packages plugins scripts

.PHONY: pylint
pylint:
	pylint -j4 aea benchmark packages scripts plugins/aea-ledger-fetchai/aea_ledger_fetchai plugins/aea-ledger-ethereum/aea_ledger_ethereum plugins/aea-ledger-cosmos/aea_ledger_cosmos plugins/aea-cli-ipfs/aea_cli_ipfs examples/*

.PHONY: security
security:
	bandit -r aea benchmark examples packages \
        plugins/aea-ledger-fetchai/aea_ledger_fetchai \
        plugins/aea-ledger-ethereum/aea_ledger_ethereum \
        plugins/aea-ledger-cosmos/aea_ledger_cosmos \
        plugins/aea-cli-ipfs/aea_cli_ipfs
	bandit -s B101 -r tests scripts
	safety check -i 37524 -i 38038 -i 37776 -i 38039 -i 39621 -i 40291 -i 39706 -i 44610 -i 50473

.PHONY: static
static:
	mypy aea benchmark examples packages plugins/aea-ledger-fetchai/aea_ledger_fetchai plugins/aea-ledger-ethereum/aea_ledger_ethereum plugins/aea-ledger-cosmos/aea_ledger_cosmos plugins/aea-cli-ipfs/aea_cli_ipfs scripts --disallow-untyped-defs
	mypy tests

.PHONY: package_checks
package_checks:
	python scripts/generate_ipfs_hashes.py --check
	python scripts/check_package_versions_in_docs.py
	python scripts/check_packages.py

.PHONY: docs
docs:
	mkdocs build --clean

.PHONY: common_checks
common_checks: security misc_checks lint static docs

.PHONY: test
test:
	pytest -rfE plugins/aea-ledger-fetchai/tests --cov=aea_ledger_fetchai --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE plugins/aea-ledger-ethereum/tests --cov=aea_ledger_ethereum --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE plugins/aea-ledger-cosmos/tests --cov=aea_ledger_cosmos --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE plugins/aea-cli-ipfs/tests --cov=aea_cli_ipfs --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE --doctest-modules aea packages/fetchai/protocols packages/fetchai/connections packages/fetchai/skills tests/ --cov=aea --cov=packages/fetchai/connections --cov=packages/fetchai/contracts --cov=packages/fetchai/protocols --cov=packages/fetchai/skills --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term --cov=aea --cov=packages/fetchai/protocols --cov=packages/fetchai/connections --cov=packages/fetchai/skills --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: test-sub
test-sub:
	pytest -rfE --doctest-modules aea packages/fetchai/connections packages/fetchai/protocols packages/fetchai/skills tests/test_$(tdir) --cov=aea.$(dir) --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term  --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: test-sub-p
test-sub-p:
	pytest -rfE --doctest-modules aea packages/fetchai/connections packages/fetchai/protocols packages/fetchai/skills tests/test_packages/test_$(tdir) --cov=packages.fetchai.$(dir) --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term  --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;


.PHONY: test-all
test-all:
	tox

.PHONY: install
install: clean
	pip install .[all]

.PHONY: dist
dist: clean
	poetry build


h := $(shell git rev-parse --abbrev-ref HEAD)

.PHONY: release_check
release:
	if [ "$h" = "main" ];\
	then\
		echo "Please ensure everything is merged into main & tagged there";\
		pip install twine;\
		twine upload dist/*;\
	else\
		echo "Please change to main branch for release.";\
	fi

v := $(shell pip -V | grep virtualenvs)

.PHONY: new_env
new_env: clean
	if [ -z "$v" ];\
	then\
		poetry install --with dev,docs,packages,tools,testing;\
		poetry run pip install -e .[all];\
		poetry run pip install --no-deps file:plugins/aea-ledger-ethereum;\
		poetry run pip install --no-deps file:plugins/aea-ledger-cosmos;\
		poetry run pip install --no-deps file:plugins/aea-ledger-fetchai;\
		poetry run pip install --no-deps file:plugins/aea-cli-ipfs;\
		echo "Enter virtual environment with all development dependencies now: 'pipenv shell'.";\
	else\
		echo "In a virtual environment! Exit first: 'exit'.";\
	fi
protolint_install:
	GO111MODULE=on GOPATH=~/go go install github.com/yoheimuta/protolint/cmd/protolint@v0.27.0
protolint:
	PATH=${PATH}:${GOPATH}/bin/:~/go/bin protolint lint -config_path=./protolint.yaml -fix ./aea/mail ./packages/fetchai/protocols
protolint_install_win:
	powershell -command '$$env:GO111MODULE="on"; go install github.com/yoheimuta/protolint/cmd/protolint@v0.27.0'
protolint_win:
	protolint lint -config_path=./protolint.yaml -fix ./aea/mail ./packages/fetchai/protocols
