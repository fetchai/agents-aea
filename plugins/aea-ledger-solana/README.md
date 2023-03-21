# Solana crypto plug-in

Solana crypto plug-in for the AEA framework.

## Install

```
pip install open-aea[all]
python setup.py install

```

## Run tests

```bash
pytest
```



## Start

```bash
PIPENV_IGNORE_VIRTUALENVS=1 && pipenv --python 3.10 && pipenv shell
```

## Pull and start testnet docker image

```bash
docker pull dassy23/solana-test-ledger:latest
```

```bash
docker run -d -p 8899:8899 -p 8900:8900 dassy23/solana-test-ledger:latest
```

