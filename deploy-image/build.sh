#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeialqqxpq3djtin7grwfl655rcsdrr4hzzu5wpifqseivcaupvrlce --remote
cd my_first_aea/
aea install
aea build
