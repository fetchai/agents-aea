#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeid76k5me2qcxpqd3ebx6obgvsa3ijxllqx4zcoa6gbv3753ifovlq --remote
cd my_first_aea/
aea install
aea build
