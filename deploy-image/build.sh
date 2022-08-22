#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny --remote
cd my_first_aea/
aea install
aea build
