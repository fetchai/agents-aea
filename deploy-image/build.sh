#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:latest --local
cd my_first_aea/
aea install
aea build
