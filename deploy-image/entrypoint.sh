#!/bin/bash
set -e

if [ -z ${AGENT_REPO_URL+x} ] ; then
        rm myagent -rf
        aea create myagent
        cd myagent
        aea add skill echo
    else
        echo "cloning $AGENT_REPO_URL inside '$(pwd)/myagent'"
        #git clone $AGENT_REPO_URL myagent
        echo git clone $AGENT_REPO_URL myagent
    fi

#/usr/local/bin/aea run
echo /usr/local/bin/aea run

while :
do
	sleep 10
    echo some log entries....
done

