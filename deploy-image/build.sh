#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeiduffhp5g7u6hdlragqnre4i3eqkdkkjukik7vjbxvhgm7ykdv5fa --remote
cd my_first_aea/
aea install
aea build
