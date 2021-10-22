FROM python:3.8-alpine

USER root

ARG USE_CLIENT
ENV USE_CLIENT=$USE_CLIENT

RUN apk add --no-cache make git bash

# cryptography: https://cryptography.io/en/latest/installation/#alpine
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev

# https://stackoverflow.com/a/57485724
RUN apk add --update --no-cache py3-numpy py3-scipy py3-pillow
ENV PYTHONPATH "${PYTHONPATH}:/usr/lib/python3.8/site-packages"

# golang
RUN apk add --no-cache go

# aea installation
RUN python -m pip install --upgrade pip
RUN pip install --upgrade --force-reinstall aea[all]==1.1.0

# directories and aea cli config
COPY /.aea /home/.aea

WORKDIR /home/agents
COPY ./packages /home/agents/packages

# aea build script
COPY /build.sh /build.sh
RUN ["chmod", "+x", "/build.sh"]
RUN [ "/build.sh" ]

# optionally, specify any ports to expose here
# EXPOSE 9000

# aea entrypoint script
COPY /entrypoint.sh /entrypoint.sh
RUN ["chmod", "+x", "/entrypoint.sh"]
CMD [ "/entrypoint.sh" ]
