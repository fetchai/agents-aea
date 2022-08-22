#!/bin/bash
set -e

# setup the agent
aea fetch --remote open_aea/my_first_aea:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny
cd my_first_aea/
aea install
aea build
