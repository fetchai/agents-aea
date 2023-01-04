#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeiewms67jpwf46u4wwh6tbzedsi5jffajnywgydeo5nlvvr6pcz2zm --remote
cd my_first_aea/
aea install
aea build
