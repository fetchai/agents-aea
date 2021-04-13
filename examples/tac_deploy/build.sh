#!/bin/bash
set -e

mkdir /data

# setup the agent
aea fetch fetchai/tac_controller:latest
cd tac_controller
aea install
aea build
cd ..

aea fetch fetchai/tac_participant:latest --alias tac_participant_template
cd tac_participant_template
aea install
aea build
cd ..

