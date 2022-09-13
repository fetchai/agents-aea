#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeifelwg4md24lwpxgx7x5cugq7ovhbkew3lxw43m52rdppfn5o5g4i --remote
cd my_first_aea/
aea install
aea build
