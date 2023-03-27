.PHONY: clean
clean: clean-test clean-build clean-pyc clean-docs

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr pip-wheel-metadata
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +
	find . -type d -name __pycache__ -exec rm -rv {} +
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
clean-test: clean-cache
	rm -fr .tox/
	rm -f .coverage
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;
	rm -fr coverage.xml
	rm -fr htmlcov/
	find . -name 'log.txt' -exec rm -fr {} +
	find . -name 'log.*.txt' -exec rm -fr {} +

# removes various cache files
.PHONY: clean-cache
clean-cache:
	rm -fr .hypothesis/
	rm -fr .pytest_cache
	rm -fr .mypy_cache/


.PHONY: package-checks
package_checks:
	tox -e hash-check
	tox -e package-version-checks
	tox -e package-dependencies-checks

.PHONY: docs
docs:
	mkdocs build --clean

.PHONY: test
test:
	pytest -rfE plugins/aea-ledger-fetchai/tests --cov=aea_ledger_fetchai --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE plugins/aea-ledger-ethereum/tests --cov=aea_ledger_ethereum --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE plugins/aea-ledger-cosmos/tests --cov=aea_ledger_cosmos --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE plugins/aea-cli-ipfs/tests --cov=aea_cli_ipfs --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	pytest -rfE --doctest-modules aea packages/valory/protocols packages/valory/connections packages/fetchai/protocols packages/fetchai/connections packages/fetchai/skills tests/ --cov=aea --cov=packages/valory/connections --cov=packages/fetchai/connections --cov=packages/fetchai/contracts --cov=packages/fetchai/protocols --cov=packages/fetchai/skills --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term --cov=aea --cov=packages/valory/protocols --cov=packages/fetchai/protocols --cov=packages/fetchai/connections --cov=packages/fetchai/skills --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: test-sub
test-sub:
	pytest -rfE --doctest-modules aea packages/valory/connections packages/valory/protocols packages/fetchai/connections packages/fetchai/protocols packages/fetchai/skills tests/test_$(tdir) --cov=aea.$(dir) --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term  --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: test-sub-p
test-sub-p:
	pytest -rfE --doctest-modules aea packages/valory/connections packages/valory/protocols packages/fetchai/connections packages/fetchai/protocols packages/fetchai/skills tests/test_packages/test_$(tdir) --cov=packages.fetchai.$(dir) --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term  --cov-config=.coveragerc
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
	WIN_BUILD_WHEEL=1 python setup.py bdist_wheel --plat-name=win_amd64
	WIN_BUILD_WHEEL=1 python setup.py bdist_wheel --plat-name=win32
	python setup.py bdist_wheel --plat-name=manylinux1_x86_64
	python setup.py bdist_wheel --plat-name=manylinux2014_aarch64
	python setup.py bdist_wheel --plat-name=macosx_10_9_x86_64

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

.PHONY: all-checks
all-checks: clean formatters code-checks generators common-checks-1 common-checks-2 security

.PHONY: new_env
new_env: clean
	if [ -z "$v" ];\
	then\
		pipenv --rm;\
		pipenv --clear;\
		pipenv --python 3.10;\
		pipenv install --dev --skip-lock;\
		pipenv run pip install -e .[all];\
		pipenv run pip install --no-deps file:plugins/aea-ledger-ethereum;\
		pipenv run pip install --no-deps file:plugins/aea-ledger-ethereum-flashbots;\
		pipenv run pip install --no-deps file:plugins/aea-ledger-cosmos;\
		pipenv run pip install --no-deps file:plugins/aea-ledger-fetchai;\
		pipenv run pip install --no-deps file:plugins/aea-cli-ipfs;\
		echo "Enter virtual environment with all development dependencies now: 'pipenv shell'.";\
		pipenv run pip install --no-deps file:plugins/aea-ledger-solana;\
	else\
		echo "In a virtual environment! Exit first: 'exit'.";\
	fi
protolint_install:
	GO111MODULE=on GOPATH=~/go go install -v github.com/yoheimuta/protolint/cmd/protolint@v0.27.0
protolint:
	PATH=${PATH}:${GOPATH}/bin/:~/go/bin protolint lint -config_path=./protolint.yaml -fix ./aea/mail ./packages/fetchai/protocols ./packages/valory/protocols
protolint_install_win:
	powershell -command '$$env:GO111MODULE="on"; go install -v github.com/yoheimuta/protolint/cmd/protolint@v0.27.0'
protolint_win:
	protolint lint -config_path=./protolint.yaml -fix ./aea/mail ./packages/fetchai/protocols ./packages/valory/protocols

# isort: fix import orders
# black: format files according to the pep standards
.PHONY: formatters
formatters:
	tox -e isort
	tox -e black

# black-check: check code style
# isort-check: check for import order
# flake8: wrapper around various code checks, https://flake8.pycqa.org/en/latest/user/error-codes.html
# mypy: static type checker
# pylint: code analysis for code smells and refactoring suggestions
# vulture: finds dead code
# darglint: docstring linter
.PHONY: code-checks
code-checks:
	tox -p -e black-check -e isort-check -e flake8 -e mypy -e pylint -e vulture -e darglint

# safety: checks dependencies for known security vulnerabilities
# bandit: security linter
.PHONY: security
security:
	tox -p -e safety -e bandit
	gitleaks detect --report-format json --report-path leak_report

# generate latest hashes for updated packages
# generate docs for updated packages
# update copyright headers
.PHONY: generators
generators: clean-cache
	rm -rf packages/fetchai/connections/stub/input_file
	tox -e fix-copyright
	tox -e lock-packages
	tox -e generate-all-protocols
	tox -e generate-api-documentation
	tox -e fix-doc-hashes

.PHONY: common-checks-1
common-checks-1:
	tox -p -e check-copyright -e hash-check -e package-dependencies-checks

.PHONY: common-checks-2
common-checks-2:
	tox -e check-api-docs
	tox -e check-doc-links-hashes
