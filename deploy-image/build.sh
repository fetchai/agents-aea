#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeib4kx5cu467tcbiy447h46ng3s3hpxk5ab7kej6c2qsavks7hnmq4 --remote
cd my_first_aea/
aea install
aea build
