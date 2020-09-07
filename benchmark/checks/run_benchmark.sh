#!/bin/bash
DATE=`LC_ALL=C date +"%d.%m.%Y_%H:%M"`
echo "Performance report for $DATE"
echo -e "-----------------------------\n"


#DURATION=10
#NUM_RUNS=100
DURATION=3
NUM_RUNS=3
MESSAGES=100


# chmod +x benchmark/checks/check_reactive.py
# echo "Reactive: number of runs: $NUM_RUNS, duration: $DURATION"
# echo "----------------------------------------------------"
# echo "runtime mode        value          mean        stdev"
# echo "----------------------------------------------------"
# for mode in threaded async;
# do
# 	data=`./benchmark/checks/check_reactive.py --duration=$DURATION --number_of_runs=$NUM_RUNS --runtime_mode=$mode`
# 	latency=`echo "$data"|grep latency|awk '{print $4 "    " $6}'`
# 	rate=`echo "$data"|grep rate|awk '{print $4 "    " $6}'`
# 	echo -e "$mode    latency     ${latency}"
# 	echo -e "$mode    rate     ${rate}"
# done
# # ~ 10 * 2 * 100 sec = 33.3 min
#
#
# chmod +x benchmark/checks/check_proactive.py
# echo -e "\nProactive: number of runs: $NUM_RUNS, duration: $DURATION"
# echo "----------------------------------------------------"
# echo "runtime mode        value          mean        stdev"
# echo "----------------------------------------------------"
# for mode in threaded async;
# do
# 	data=`./benchmark/checks/check_proactive.py --duration=$DURATION --number_of_runs=$NUM_RUNS --runtime_mode=$mode`
# 	latency=`echo "$data"|grep latency|awk '{print $4 "    " $6}'`
# 	rate=`echo "$data"|grep rate|awk '{print $4 "    " $6}'`
# 	echo -e "$mode    rate     ${rate}"
# done
# # ~ 10 * 2 * 100 sec = 33.3 min

chmod +x benchmark/checks/check_multiagent.py
echo -e "\nMultiAgent: number of runs: $NUM_RUNS, duration: $DURATION, messages: $MESSAGES"
echo "------------------------------------------------------------------"
echo "runtime mode     num_agents       value          mean        stdev"
echo "------------------------------------------------------------------"
for mode in threaded async;
do
	for agent in 2 4 8 16;
	do
		data=`./benchmark/checks/check_multiagent.py --num_of_agents=$agent --duration=$DURATION --number_of_runs=$NUM_RUNS --runtime_mode=$mode --start_messages=$MESSAGES --runner_mode=threaded`
		rate=`echo "$data"|grep rate|awk '{print $5 "    " $7}'`
		mem=`echo "$data"|grep Mem|awk '{print $5 "    " $7}'`
		rtt_latency=`echo "$data"|grep 'RTT'|awk '{print $5 "    " $7}'`
		latency=`echo "$data"|grep 'Latency'|awk '{print $5 "    " $7}'`
		echo -e "$mode     $agent    rate     ${rate}"
		echo -e "$mode     $agent    mem     ${mem}"
		echo -e "$mode     $agent    RTT     ${rtt_latency}"
		echo -e "$mode     $agent    latency     ${latency}"
	done
done
# ~ 10 * 2 * 4 * 100 sec = 133.3 min
