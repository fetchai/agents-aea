#!/bin/bash
set -e

aea --version

if [ -z ${AGENT_REPO_URL+x} ] ; then
        rm myagent -rf
        aea fetch fetchai/my_first_aea:0.10.0
        cd my_first_aea
    else
        echo "cloning $AGENT_REPO_URL inside '$(pwd)/my_aea'"
        echo git clone $AGENT_REPO_URL my_aea
        git clone $AGENT_REPO_URL my_aea && cd my_aea
    fi

echo /usr/local/bin/aea run
/usr/local/bin/aea run
