#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeihhrlcmu6dibftsg36m47uxi4inltsjvmoip5smvevq3caiwm3oo4 --remote
cd my_first_aea/
aea install
aea build
