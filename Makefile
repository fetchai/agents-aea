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
	black aea benchmark examples packages plugins scripts tests
	isort aea benchmark examples packages plugins scripts tests
	flake8 aea benchmark examples packages plugins scripts tests
	vulture aea scripts/whitelist.py --exclude "*_pb2.py"

.PHONY: pylint
pylint:
	pylint -j4 aea benchmark packages scripts plugins/aea-crypto-fetchai/aea_crypto_fetchai plugins/aea-crypto-ethereum/aea_crypto_ethereum plugins/aea-crypto-cosmos/aea_crypto_cosmos examples/*

.PHONY: security
security:
	bandit -r aea benchmark examples packages \
        plugins/aea-crypto-fetchai/aea_crypto_fetchai \
        plugins/aea-crypto-ethereum/aea_crypto_ethereum \
        plugins/aea-crypto-cosmos/aea_crypto_cosmos
	bandit -s B101 -r tests scripts \
        plugins/aea-crypto-fetchai/tests \
        plugins/aea-crypto-ethereum/tests \
        plugins/aea-crypto-cosmos/tests
	safety check -i 37524 -i 38038 -i 37776 -i 38039

.PHONY: static
static:
	mypy aea benchmark examples packages plugins/aea-crypto-fetchai/aea_crypto_fetchai plugins/aea-crypto-ethereum/aea_crypto_ethereum plugins/aea-crypto-cosmos/aea_crypto_cosmos scripts --disallow-untyped-defs
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
	pytest -rfE plugins/aea-crypto-fetchai/tests --cov=aea_crypto_fetchai --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE plugins/aea-crypto-ethereum/tests --cov=aea_crypto_ethereum --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE plugins/aea-crypto-cosmos/tests --cov=aea_crypto_cosmos --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE --doctest-modules aea packages/fetchai/protocols packages/fetchai/connections packages/fetchai/skills/confirmation_aw1 packages/fetchai/skills/confirmation_aw2 packages/fetchai/skills/confirmation_aw3 packages/fetchai/skills/generic_buyer packages/fetchai/skills/generic_seller packages/fetchai/skills/tac_control packages/fetchai/skills/tac_control_contract packages/fetchai/skills/tac_participation packages/fetchai/skills/tac_negotiation packages/fetchai/skills/simple_buyer packages/fetchai/skills/simple_data_request packages/fetchai/skills/simple_seller packages/fetchai/skills/simple_service_registration packages/fetchai/skills/simple_service_search packages/fetchai/skills/coin_price packages/fetchai/skills/fetch_beacon packages/fetchai/skills/simple_oracle packages/fetchai/skills/simple_oracle_client tests/ --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term --cov=aea --cov=packages/fetchai/protocols --cov=packages/fetchai/connections --cov=packages/fetchai/skills/confirmation_aw1 --cov=packages/fetchai/skills/confirmation_aw2 --cov=packages/fetchai/skills/confirmation_aw3 --cov=packages/fetchai/skills/generic_buyer --cov=packages/fetchai/skills/generic_seller --cov=packages/fetchai/skills/tac_control --cov=packages/fetchai/skills/tac_control_contract --cov=packages/fetchai/skills/tac_participation --cov=packages/fetchai/skills/tac_negotiation --cov=packages/fetchai/skills/simple_buyer --cov=packages/fetchai/skills/simple_data_request --cov=packages/fetchai/skills/simple_seller --cov=packages/fetchai/skills/simple_service_registration --cov=packages/fetchai/skills/simple_service_search --cov=packages/fetchai/skills/coin_price --cov=packages/fetchai/skills/fetch_beacon --cov=packages/fetchai/skills/simple_oracle --cov=packages/fetchai/skills/simple_oracle_client --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: test-sub
test-sub:
	pytest -rfE --doctest-modules aea packages/fetchai/connections packages/fetchai/protocols packages/fetchai/skills/confirmation_aw1 packages/fetchai/skills/confirmation_aw2 packages/fetchai/skills/confirmation_aw3 packages/fetchai/skills/generic_buyer packages/fetchai/skills/generic_seller packages/fetchai/skills/tac_control packages/fetchai/skills/tac_control_contract packages/fetchai/skills/tac_participation packages/fetchai/skills/tac_negotiation tests/test_$(tdir) --cov=aea.$(dir) --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term  --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: test-sub-p
test-sub-p:
	pytest -rfE --doctest-modules aea packages/fetchai/connections packages/fetchai/protocols packages/fetchai/skills/confirmation_aw1 packages/fetchai/skills/confirmation_aw2 packages/fetchai/skills/confirmation_aw3 packages/fetchai/skills/generic_buyer packages/fetchai/skills/generic_seller packages/fetchai/skills/tac_control packages/fetchai/skills/tac_control_contract packages/fetchai/skills/tac_participation packages/fetchai/skills/tac_negotiation packages/fetchai/skills/simple_buyer packages/fetchai/skills/simple_data_request packages/fetchai/skills/simple_seller packages/fetchai/skills/simple_service_registration packages/fetchai/skills/simple_service_search packages/fetchai/skills/coin_price packages/fetchai/skills/fetch_beacon packages/fetchai/skills/simple_oracle packages/fetchai/skills/simple_oracle_client tests/test_packages/test_$(tdir) --cov=packages.fetchai.$(dir) --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term  --cov-config=.coveragerc
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
		pipenv --rm;\
		pipenv --python 3.7;\
		pipenv install --dev --skip-lock;\
		pipenv run pip uninstall typing -y;\
		pipenv run pip install -e .[all];\
		pipenv run pip install --no-deps file:plugins/aea-crypto-ethereum;\
		pipenv run pip install --no-deps file:plugins/aea-crypto-cosmos;\
		pipenv run pip install --no-deps file:plugins/aea-crypto-fetchai;\
		echo "Enter virtual environment with all development dependencies now: 'pipenv shell'.";\
	else\
		echo "In a virtual environment! Exit first: 'exit'.";\
	fi
protolint_install:
	GO111MODULE=on GOPATH=~/go go get -u -v github.com/yoheimuta/protolint/cmd/protolint@v0.27.0
protolint:
	PATH=${PATH}:${GOPATH}/bin/:~/go/bin protolint lint -config_path=./protolint.yaml -fix ./aea/mail ./packages/fetchai/protocols
protolint_install_win:
	powershell -command '$$env:GO111MODULE="on"; go get -u -v github.com/yoheimuta/protolint/cmd/protolint@v0.27.0'
protolint_win:
	protolint lint -config_path=./protolint.yaml -fix ./aea/mail ./packages/fetchai/protocols
