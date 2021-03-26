#!/bin/bash
set -e

aea --version

cd my_first_aea

# create private key files
echo ${AGENT_PRIV_KEY} > fetchai_private_key.txt
echo ${CONNECTION_PRIV_KEY} > connection_fetchai_private_key.txt

# add keys
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai connection_fetchai_private_key.txt --connection

# issue certs
aea issue-certificates

# run
aea run
