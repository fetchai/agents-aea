#!/bin/bash

# setup the agent
aea fetch fetchai/my_first_aea:latest
cd my_first_aea/
aea install
aea build
