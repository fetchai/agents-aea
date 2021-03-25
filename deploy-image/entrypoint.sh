#!/bin/bash
set -e

aea --version

# add private keys
printf ${AGENT_PRIV_KEY} > fetchai_private_key.txt
printf ${P2P_PRIV_KEY} > p2p_private_key.txt
aea add-key fetchai 
aea add-key fetchai p2p_private_key.txt --connection

# issue certs
aea issue-certificates

# run
aea run
