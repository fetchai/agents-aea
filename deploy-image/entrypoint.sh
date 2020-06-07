#!/bin/bash
set -e

if [ -z ${AGENT_REPO_URL+x} ] ; then
        rm myagent -rf
        aea create myagent
        cd myagent
        aea add skill fetchai/echo:0.2.0
    else
        echo "cloning $AGENT_REPO_URL inside '$(pwd)/myagent'"
        echo git clone $AGENT_REPO_URL myagent
        git clone $AGENT_REPO_URL myagent && cd myagent
    fi

echo /usr/local/bin/aea run
/usr/local/bin/aea run
