#!/bin/bash
set -e

LEDGER=fetchai
PEER="/dns4/acn.fetch.ai/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW"
TAC_NAME='v'$((10 + $RANDOM % 1000))
TAC_SERVICE=tac_service_$TAC_NAME
BASE_PORT=10000
BASE_DIR=/data
OLD_DIR=/$(date "+%d_%m_%Y_%H%M")

cp -R "$BASE_DIR" "$OLD_DIR"

if [ -z  "$COMPETITION_TIMEOUT" ];
then
	COMPETITION_TIMEOUT=86400
fi
echo COMPETITION_TIMEOUT $COMPETITION_TIMEOUT

if [ -z  "$INACTIVITY_TIMEOUT" ];
then
	INACTIVITY_TIMEOUT=3600
fi
echo INACTIVITY_TIMEOUT $INACTIVITY_TIMEOUT

if [ -z  "$PARTICIPANTS_AMOUNT" ];
then
	PARTICIPANTS_AMOUNT=2
fi
echo PARTICIPANTS_AMOUNT $PARTICIPANTS_AMOUNT


if [ -z  "$MINUTES_TILL_START" ];
then
	MINUTES_TILL_START=2
fi
echo MINUTES_TILL_START $MINUTES_TILL_START

if [ -z  "$SEARCH_INTERVAL_GAME" ];
then
	SEARCH_INTERVAL_GAME=20
fi
echo SEARCH_INTERVAL_GAME $SEARCH_INTERVAL_GAME

if [ -z  "$SEARCH_INTERVAL_TRADING" ];
then
	SEARCH_INTERVAL_TRADING=600
fi
echo SEARCH_INTERVAL_TRADING $SEARCH_INTERVAL_TRADING

if [ -z  "$CLEANUP_INTERVAL" ];
then
	CLEANUP_INTERVAL=1800
fi
echo CLEANUP_INTERVAL $CLEANUP_INTERVAL

if [ -z  "$NODE_CONNECTION_TIMEOUT" ];
then
	NODE_CONNECTION_TIMEOUT=30
fi
echo NODE_CONNECTION_TIMEOUT $NODE_CONNECTION_TIMEOUT

if [ -z  "$LOG_LEVEL" ];
then
	LOG_LEVEL=INFO
fi
echo LOG_LEVEL $LOG_LEVEL

if [ -z  "$CLEAR_LOG_DATA_ON_LAUNCH" ];
then
	CLEAR_LOG_DATA_ON_LAUNCH=true
fi
echo CLEAR_LOG_DATA_ON_LAUNCH $CLEAR_LOG_DATA_ON_LAUNCH

if [ -z  "$CLEAR_KEY_DATA_ON_LAUNCH" ];
then
	CLEAR_KEY_DATA_ON_LAUNCH=false
fi
echo CLEAR_KEY_DATA_ON_LAUNCH $CLEAR_KEY_DATA_ON_LAUNCH

if [ "$CLEAR_LOG_DATA_ON_LAUNCH" == true ]; then
	find "$BASE_DIR" -name \*.log -type f -delete
fi

if [ "$CLEAR_KEY_DATA_ON_LAUNCH" == true ]; then
	find "$BASE_DIR" -name \*.txt -type f -delete
fi

if [ -z "$USE_CLIENT" ]; then
	USE_CLIENT=false
fi

function generate_key (){
	ledger=$1
	prefix=$2
	base_dir=$3
	connection=$4
	if [ $connection = '1' ];
	then
		connection='_connection'
	else
		connection=''
	fi
	filename="${base_dir}/${prefix}_${ledger}${connection}_private_key.txt"
	
	if [ -e "${filename}" ];
	then
		echo > /dev/null
	else
	 aea generate-key $ledger $filename $con_option
	fi
	echo ${filename}
}

function set_agent(){
	name=$1
	port=$2
	echo name $name port $port
	agent_data_dir=$BASE_DIR/$name
	mkdir -p $agent_data_dir
	key_file_name=$(generate_key $LEDGER $name $agent_data_dir 0)
	aea add-key fetchai $key_file_name	
	key_file_name=$(generate_key $LEDGER $name $agent_data_dir 1)
	aea add-key fetchai $key_file_name --connection
	if [ "$USE_CLIENT" == "false" ];
	then
		json=$(printf '{"log_file": "%s", "delegate_uri": null, "entry_peers": ["%s"], "local_uri": "127.0.0.1:%s", "public_uri": null, "node_connection_timeout": '%i'}' "$agent_data_dir/libp2p_node.log" "$PEER" "$port" "$(($NODE_CONNECTION_TIMEOUT))")
		aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config "$json"
	fi
	aea issue-certificates
	log_file=$agent_data_dir/$name.log
	json=$(printf '{"version": 1, "formatters": {"standard": {"format": ""}}, "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "standard", "level": "%s"}, "file": {"class": "logging.FileHandler", "filename": "%s", "mode": "w", "level": "%s", "formatter": "standard"}}, "loggers": {"aea": {"level": "%s", "handlers": ["file"]}}}' "$LOG_LEVEL" "$log_file" "$LOG_LEVEL" "$LOG_LEVEL")
	aea config set --type dict agent.logging_config "$json"
	aea config set agent.logging_config.formatters.standard.format '%(asctime)s [%(levelname)s]: %(message)s'
	aea config set vendor.fetchai.connections.soef.config.token_storage_path $agent_data_dir/soef_token.txt
	aea config set agent.skill_exception_policy just_log
	aea config set agent.connection_exception_policy just_log
}

function set_tac_name (){
	json=$(printf '{"key": "tac", "value": "%s"}' $TAC_NAME)
	aea config set --type dict vendor.fetchai.skills.tac_control.models.parameters.args.service_data "$json"
}

function set_participant(){
	agent_id=$1
	agent_name=$2
	echo "cp -r tac_participant_template $agent_name"
	cp -r tac_participant_template $agent_name
	cd $agent_name
	# cause set agent name is not allowed!
	sed -e "s/tac_participant_template/$agent_name/" -i ./aea-config.yaml
	set_agent $agent_name $(expr $BASE_PORT + $agent_id)
	aea config set vendor.fetchai.skills.tac_negotiation.behaviours.clean_up.args.tick_interval $CLEANUP_INTERVAL
	aea config set vendor.fetchai.skills.tac_negotiation.behaviours.tac_negotiation.args.search_interval $SEARCH_INTERVAL_TRADING
	aea config set vendor.fetchai.skills.tac_negotiation.models.strategy.args.service_key $TAC_SERVICE
	aea config set vendor.fetchai.skills.tac_participation.behaviours.tac_search.args.tick_interval $SEARCH_INTERVAL_GAME
	aea config set vendor.fetchai.skills.tac_participation.models.game.args.search_query.search_value $TAC_NAME
	cd ..
}

agents_list=''
for i in $(seq $PARTICIPANTS_AMOUNT);
do
	agent_name="tac_participant_$i"
	set_participant $i $agent_name
	agents_list="$agent_name $agents_list"
done

cd tac_controller
set_agent tac_controller $BASE_PORT
set_tac_name
datetime_start=$(date -d@"$(( `date +%s`+$MINUTES_TILL_START*60))" "+%d %m %Y %H:%M")
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time "$datetime_start"
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.competition_timeout $COMPETITION_TIMEOUT
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.inactivity_timeout $INACTIVITY_TIMEOUT
cd ..

echo "Launching agents..."
aea launch tac_controller $agents_list
