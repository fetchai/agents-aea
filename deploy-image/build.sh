#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeiaxmuyuyi3artliclevp2akaccuptu63ioxzp43qa66s74brhz74m --remote
cd my_first_aea/
aea install
aea build
