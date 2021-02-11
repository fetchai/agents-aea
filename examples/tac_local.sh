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

entry_peer="/dns4/acn.fetch.ai/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW"
tac_name=v1_$identifier

echo "Creating controller..."
rm -rf tac_controller
aea fetch --local fetchai/tac_controller:latest
cd tac_controller
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
json=$(printf '{"delegate_uri": null, "entry_peers": ["%s"], "local_uri": "127.0.0.1:10000", "public_uri": null}' "$entry_peer")
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config "$json"
aea config get vendor.fetchai.connections.p2p_libp2p.config
# multiaddress=$(aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.12.0 -u public_uri)
json=$(printf '{"key": "tac", "value": "%s"}' $tac_name)
aea config set --type dict vendor.fetchai.skills.tac_control.models.parameters.args.service_data "$json"
aea config get vendor.fetchai.skills.tac_control.models.parameters.args.service_data
aea install
aea build
aea issue-certificates
cd ..

empty_lines
echo "Creating participants..."
agents=""
for i in $(seq $participants);
do
agent=tac_participant_$i
agents=$(echo $agent $agents)
rm -rf $agent
aea fetch --local fetchai/tac_participant:latest --alias $agent
cd $agent
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
json=$(printf '{"delegate_uri": null, "entry_peers": ["%s"], "local_uri": "127.0.0.1:1%0.4d", "public_uri": null}' "$entry_peer" "$i")
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config "$json"
aea config get vendor.fetchai.connections.p2p_libp2p.config
aea config set vendor.fetchai.skills.tac_participation.models.game.args.search_query.search_value $tac_name
aea config get vendor.fetchai.skills.tac_participation.models.game.args.search_query
aea install
aea build
aea issue-certificates
cd ..
done

empty_lines
time_diff=$(printf '+%sM' "$min")
datetime_now=$(date "+%d %m %Y %H:%M")
datetime_start=$(date -v $time_diff "+%d %m %Y %H:%M")
# '01 01 2020  00:01'
echo "Now:" $datetime_now "Start:" $datetime_start
cd tac_controller
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time "$datetime_start"
echo "Start time set:" $(aea config get vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time)
cd ..

empty_lines
echo "Running agents..."
aea launch tac_controller $agents
