#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeia2h6uk25aktvzwle3nbdex7iqkf4nktgp2w2b6qbqqj3za7h7d24 --remote
cd my_first_aea/
aea install
aea build
