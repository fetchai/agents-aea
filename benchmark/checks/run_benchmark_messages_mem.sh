#!/bin/bash
DATE=`LC_ALL=C date +"%d.%m.%Y_%H:%M"`
echo "Performance report for $DATE"
echo -e "-----------------------------\n"

AGENTS=10
NUM_RUNS=10
MESSAGES=100
RUNNER_MODE=threaded

# check memory usage in terms of duration
chmod +x benchmark/checks/check_multiagent_http_dialogues.py
echo -e "\n\nMulti agents with http dialogues: number of runs: $NUM_RUNS, num_agents: $AGENTS, messages: $MESSAGES"
echo "------------------------------------------------------------------"
echo "runtime mode     duration       value          mean        stdev"
echo "------------------------------------------------------------------"
for runtime_mode in async;
do
	for duration in 2 5 10 20 30 50;
	do
		cmd="./benchmark/checks/check_multiagent_http_dialogues.py --num_of_agents=$AGENTS --duration=$duration --number_of_runs=$NUM_RUNS --runtime_mode=$runtime_mode --start_messages=$MESSAGES --runner_mode=$RUNNER_MODE"
		data=`$cmd 2>>/dev/null`
		rate=`echo "$data"|grep rate|awk '{print $5 "    " $7}'`
		mem=`echo "$data"|grep Mem|awk '{print $5 "    " $7}'`
		rtt_latency=`echo "$data"|grep 'RTT'|awk '{print $5 "    " $7}'`
		latency=`echo "$data"|grep 'Latency'|awk '{print $5 "    " $7}'`
		#echo -e "$runtime_mode     $duration    rate     ${rate}"
		echo -e "$runtime_mode\t\t     $duration\t\t    mem\t     ${mem}"
		#echo -e "$runtime_mode     $duration    RTT     ${rtt_latency}"
		#echo -e "$runtime_mode     $duration    latency     ${latency}"
	done
done



# check memory usage in terms of duration
chmod +x benchmark/checks/check_messages_memory_usage.py
echo -e "\n\nMessage generation and allocation: number of runs: $NUM_RUNS"
echo "------------------------------------------------------------------"
echo "message        value          mean        stdev"
echo "------------------------------------------------------------------"
for messages in 10000 50000 100000;
do
	cmd="./benchmark/checks/check_messages_memory_usage.py --messages=$messages --number_of_runs=$NUM_RUNS"
	data=`$cmd 2>>/dev/null`
	time=`echo "$data"|grep Time|awk '{print $5 "    " $7}'`
	mem=`echo "$data"|grep Mem|awk '{print $5 "    " $7}'`
	echo -e "$messages\t\t    mem\t     ${mem}"
	echo -e "$messages\t\t    time     ${time}"
done



# check memory usage in terms of duration
chmod +x benchmark/checks/check_dialogues_memory_usage.py
echo -e "\n\nDialogues message processing: number of runs: $NUM_RUNS"
echo "------------------------------------------------------------------"
echo "message        value          mean        stdev"
echo "------------------------------------------------------------------"
for messages in 10000 20000 50000;
do
	cmd="./benchmark/checks/check_dialogues_memory_usage.py --messages=$messages --number_of_runs=$NUM_RUNS"
	data=`$cmd 2>>/dev/null`
	time=`echo "$data"|grep Time|awk '{print $5 "    " $7}'`
	mem=`echo "$data"|grep Mem|awk '{print $5 "    " $7}'`
	echo -e "$messages\t\t    mem\t     ${mem}"
	echo -e "$messages\t\t    time     ${time}"
done
