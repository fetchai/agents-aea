#!/bin/bash
set -e

# setup the agent
aea fetch open_aea/my_first_aea:0.1.0:bafybeihpi4lbgdnjkwpgf5qpyfovs6vtvgikkr6lkhmy6w6stsuohoymwy --remote
cd my_first_aea/
aea install
aea build
