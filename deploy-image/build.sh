#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeieosuwomgx5mviv2jposmwf7xaau33mjrllgvasnipyvsw2eok3yu --remote
cd my_first_aea/
aea install
aea build
