#!/bin/bash
set -e

if [ -z "$USE_CLIENT" ];
then
	USE_CLIENT=false
fi
echo USE_CLIENT $USE_CLIENT

if [ -z "$PACKAGES_SOURCE" ];
then
	PACKAGES_SOURCE="--remote"
fi
echo PACKAGES_SOURCE $PACKAGES_SOURCE

mkdir /data

# setup the agent
aea fetch $PACKAGES_SOURCE fetchai/tac_controller:latest
cd tac_controller
if [[ "$USE_CLIENT" == "true" ]]
then
	aea remove connection fetchai/p2p_libp2p
	aea add $PACKAGES_SOURCE connection fetchai/p2p_libp2p_client
	aea config set agent.default_connection fetchai/p2p_libp2p_client:0.18.0
fi
aea install
aea build
cd ..

aea fetch $PACKAGES_SOURCE fetchai/tac_participant:latest --alias tac_participant_template
cd tac_participant_template
if [[ "$USE_CLIENT" == "true" ]]
then
	aea remove connection fetchai/p2p_libp2p
	aea add $PACKAGES_SOURCE connection fetchai/p2p_libp2p_client
	aea config set agent.default_connection fetchai/p2p_libp2p_client:0.18.0
fi
aea install
aea build
cd ..

