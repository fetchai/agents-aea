#!/bin/bash -e
datetime=$1
# '01 01 2020  00:01'
participants=$2
# 2

if [ -z "$datetime" ];
    then exit 1;
fi

if [ -z "$participants" ];
    then exit 1;
fi

# create working dir
folder=tac_$(date "+%d_%m_%H%M")
mkdir $folder
cd $folder

# create controller
aea fetch fetchai/tac_controller:0.15.0
cd tac_controller
aea install
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time "$datetime"
aea config get vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time
multiaddress=$(aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.12.0 -u public_uri)
cd ..

# create participants
agents=""
for i in $(seq $participants);
do
agent=tac_participant_$i
agents=$(echo $agent $agents)
aea fetch fetchai/tac_participant:0.17.0 --alias $agent
cd $agent
json=$(printf '{"delegate_uri": null, "entry_peers": ["%s"], "local_uri": "127.0.0.1:1%0.4d", "public_uri": null}' "$multiaddress" "$i")
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config "$json"
aea config get vendor.fetchai.connections.p2p_libp2p.config
aea install
cd ..
done

# run agents
aea launch tac_controller $agents