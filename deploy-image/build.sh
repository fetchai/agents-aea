#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeibbciu53bz3izf2v5vxtveykzwm5zfzpkzoxtlh5qzyemvksiijje --remote
cd my_first_aea/
aea install
aea build
