#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeidqq73k63tr5baafodg3w5xy3g5so45k5wn2rpo7plkeiq3ojdxfu --remote
cd my_first_aea/
aea install
aea build
