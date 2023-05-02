FROM python:3.10-alpine

USER root

RUN apk add --no-cache make git bash

# cryptography: https://cryptography.io/en/latest/installation/#alpine
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev

# https://stackoverflow.com/a/57485724
RUN apk add --update --no-cache py3-numpy py3-scipy py3-pillow
ENV PYTHONPATH "$PYTHONPATH:/usr/lib/python3.10/site-packages"

# golang
RUN apk add --no-cache go

# aea installation
RUN pip install --upgrade pip
RUN pip install --upgrade --force-reinstall open-aea[all]==1.33.0 "open-aea-cli-ipfs<2.0.0,>=1.33.0"

# directories and aea cli config
WORKDIR /home/agents
RUN pip install --upgrade setuptools
RUN aea init --reset --author default_author --remote --ipfs --ipfs-node /dns/registry.autonolas.tech/tcp/443/https

# aea build script
COPY deploy-image/build.sh /build.sh
RUN ["chmod", "+x", "/build.sh"]
RUN [ "/build.sh" ]

# optionally, specify any ports to expose here
# EXPOSE 9000

# aea entrypoint script
COPY deploy-image/entrypoint.sh /entrypoint.sh
RUN ["chmod", "+x", "/entrypoint.sh"]
CMD [ "/entrypoint.sh" ]
