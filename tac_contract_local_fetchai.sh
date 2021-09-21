#!/bin/bash -e
min=$1
# 2
participants=$2
# 2
identifier=$3
# some string

if [ -z "$min" ];
    then echo "No minutes provided"; exit 1;
fi

if [ -z "$participants" ];
    then echo "No participants provided"; exit 1;
fi

# helper
function empty_lines {
  for i in {1..2}
  do
    echo ""
  done
}

#not used cause local peer set in tac controller
#entry_peer="/dns4/acn.fetch.ai/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW"

tac_name=v1_$identifier

echo "Creating controller..."
rm -rf tac_controller_contract
aea fetch --local fetchai/tac_controller_contract:latest
cd tac_controller_contract
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
json=$(printf '{"delegate_uri": null, "entry_peers": [], "local_uri": "127.0.0.1:10000", "public_uri": "127.0.0.1:10000"}')
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config "$json"
aea config get vendor.fetchai.connections.p2p_libp2p.config
# multiaddress=$(aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.12.0 -u public_uri)
json=$(printf '{"key": "tac", "value": "%s"}' $tac_name)
aea config set --type dict vendor.fetchai.skills.tac_control_contract.models.parameters.args.service_data "$json"
aea config get vendor.fetchai.skills.tac_control_contract.models.parameters.args.service_data
aea install
aea build
aea issue-certificates
PEER=`aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.24.0 -u public_uri`
cd ..

empty_lines
echo "Creating participants..."
agents=""
for i in $(seq $participants);
do
agent=tac_participant_$i
agents=$(echo $agent $agents)
rm -rf $agent
aea -s fetch --local fetchai/tac_participant_contract:latest --alias $agent
cd $agent
aea -s generate-key fetchai
aea -s add-key fetchai fetchai_private_key.txt
aea -s generate-key fetchai fetchai_connection_private_key.txt
aea -s add-key fetchai fetchai_connection_private_key.txt --connection
json=$(printf '{"delegate_uri": null, "entry_peers": ["%s"], "local_uri": "127.0.0.1:1%0.4d", "public_uri": null}' "$PEER" "$i")
aea -s config set --type dict vendor.fetchai.connections.p2p_libp2p.config "$json"
aea -s config get vendor.fetchai.connections.p2p_libp2p.config
aea -s config set vendor.fetchai.skills.tac_participation.models.game.args.search_query.search_value $tac_name
aea -s config get vendor.fetchai.skills.tac_participation.models.game.args.search_query
aea -s install
aea -s build
aea -s issue-certificates
cd ..
done

empty_lines
time_diff=$(printf '+%sM' "$min")
datetime_now=$(date "+%d %m %Y %H:%M")
datetime_start=$([ "$(uname)" = Linux ] && date --date="$min minutes" "+%d %m %Y %H:%M" ||date -v $time_diff "+%d %m %Y %H:%M")
# '01 01 2020  00:01'
echo "Now:" $datetime_now "Start:" $datetime_start
cd tac_controller_contract
aea config set vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time "$datetime_start"
echo "Start time set:" $(aea config get vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time)
cd ..

empty_lines
#echo "Running agents..."
#aea launch tac_controller $agents
