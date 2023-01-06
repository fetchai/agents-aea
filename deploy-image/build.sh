#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeicls2nlbcjqisieuj7sxhcnjjfsiopvid3seqxuordj6wfsenuxma --remote
cd my_first_aea/
aea install
aea build
