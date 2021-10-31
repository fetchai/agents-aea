#!/bin/bash
REPO=https://github.com/valory-xyz/open-aea.git
BRANCH=main
TMP_DIR=$(mktemp -d -t bench-XXXXXXXXXX)
git clone --branch $BRANCH $REPO $TMP_DIR

CURDIR=`pwd`
cd $TMP_DIR

echo "Installing the dependencies."
pip install pipenv
# this is to install benchmark dependencies
pipenv --rm
pipenv install --dev --skip-lock
# this is to install the AEA in the Pipenv virtual env
pipenv run pip install --upgrade .[all] -y
pipenv run pip uninstall typing -y
pipenv run pip install --no-deps open-aea-ledger-fetchai -y
pipenv run pip install --no-deps open-aea-ledger-cosmos -y
pipenv run pip install --no-deps open-aea-ledger-ethereum -y

chmod +x benchmark/checks/run_benchmark.sh
echo "Start the experiments."
# we need to add the current directory to PYTHONPATH so we can import from local dirs
PYTHONPATH=${PYTHONPATH}:$TMP_DIR pipenv run ./benchmark/checks/run_benchmark.sh

rm -fr $TMPDIR
cd $CURDIR

echo "Done!"
