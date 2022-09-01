#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeih7n7c3j24cd4ioycwt5a4fgfmj4u7l6r5yww5o2tzh236pgrpmjy --remote
cd my_first_aea/
aea install
aea build
