#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeida2z2lk63dq555g72oio6salsgg36k66zndjius6ujlevomby3l4 --remote
cd my_first_aea/
aea install
aea build
