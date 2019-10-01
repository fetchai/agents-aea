FROM python:3.7-alpine

RUN apk add --no-cache make git bash

# cryptography: https://cryptography.io/en/latest/installation/#alpine
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev

# https://stackoverflow.com/a/57485724
RUN apk add --update --no-cache py3-numpy py3-scipy py3-pillow py3-zmq
ENV PYTHONPATH "$PYTHONPATH:/usr/lib/python3.7/site-packages"

RUN pip install --upgrade pip
# other oef dependences
RUN pip install protobuf colorlog graphviz
RUN pip install aea[all]

COPY ./packages /home/packages
WORKDIR home

ARG AGENT_REPO_URL=""

RUN if [ -z ${AGENT_REPO_URL+x} ] ; then\
        rm myagent -rf &&\
        aea create myagent &&\
        cd myagent &&\
        aea add skill echo;\
    else \
        echo "cloning $AGENT_REPO_URL inside '$(pwd)/myagent'" &&\
        git clone $AGENT_REPO_URL myagent;\
    fi

WORKDIR /home/myagent
CMD ["/usr/local/bin/aea", "run"]
