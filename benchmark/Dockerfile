FROM python:3.8-alpine

ENV PYTHONPATH "$PYTHONPATH:/usr/lib/python3.8/site-packages"
RUN apk add --no-cache make git bash wget
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev
RUN apk add --update --no-cache py3-numpy py3-scipy py3-pillow
RUN apk add --update --no-cache gfortran freetype-dev libpng-dev openblas-dev g++ py3-numpy-dev
RUN apk add --no-cache go rust cargo

RUN pip install --upgrade pip pipenv
RUN pip install aea[all] --upgrade --force-reinstall

RUN wget https://raw.githubusercontent.com/fetchai/agents-aea/main/Pipfile
RUN pipenv install -d --deploy --skip-lock --system
RUN pip install --no-deps  aea-ledger-fetchai
RUN pip install --no-deps  aea-ledger-cosmos
RUN pip install --no-deps  aea-ledger-ethereum
