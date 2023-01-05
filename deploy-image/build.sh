#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeieaobewnqovei7qv66puhr4e56y47h6rxt7jpnddudx7tzlh5r6ri --remote
cd my_first_aea/
aea install
aea build
