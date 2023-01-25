#!/bin/bash -e
# Usage:
#   ./docker-build-img.sh <IMMEDIATE_PARAMS> -- <TAIL_PARAMS>
# Where:
#  * resulting docker build commandline will be:
#    docker build $IMMEDIATE_PARAMS -t $DOCKER_IMAGE_TAG $TAIL_PARAMS $DOCKER_BUILD_CONTEXT_DIR
#  * DOCKER_IMAGE_TAG and DOCKER_BUILD_CONTEXT_DIR variables are defined in the `docker-env.sh` and/or `docker-env-common.sh`
#
# Examples:
#  * the following example provides the `--cpus 4 --compress` parameters to `docker build` command as IMMEDIATE_PARAMS, **ommiting** the TAIL_PARAMS:
#
#    ./docker-build-img.sh --cpus 4 ---compress --
#    # the the resulting docker process commandline will be:
#    #   docker build --cpus 4 --compress -t $DOCKER_IMAGE_TAG $TAIL_PARAMS $DOCKER_BUILD_CONTEXT_DIR
#
#  * the following example provides the `--squash` parameters to `docker build` command as IMMEDIATE_PARAMS, and `../../` parameter as TAIL_PARAMS (what corresponds to the context directory, what also means that DOCKER_BUILD_CONTEXT_DIR variable needs to be unset or set to empty string in the `docker-env.sh`):
#
#    ./docker-build-img.sh --squash -- ../../
#    # the the resulting docker process commandline will be:
#    #   docker build --squash -t $DOCKER_IMAGE_TAG ../../ $DOCKER_BUILD_CONTEXT_DIR
#    # the `DOCKER_BUILD_CONTEXT_DIR` shall be set to empty string in `docker-env.sh` file.
# NOTE: For more details, please see description for the `split_params()` shell function in the `docker-common.sh` script.

SCRIPTS_DIR=${0%/*}
. "$SCRIPTS_DIR"/docker-env-common.sh

docker_build_callback() {
    local IMMEDIATE_PARAMS="$1"
    local TAIL_PARAMS="$2"

    if [ -n "${DOCKERFILE}" ]; then
        TAIL_PARAMS="-f $DOCKERFILE $TAIL_PARAMS"
    fi

    local COMMAND="docker build $IMMEDIATE_PARAMS -t $DOCKER_IMAGE_TAG $TAIL_PARAMS $DOCKER_BUILD_CONTEXT_DIR"

    echo $COMMAND
    $COMMAND
}

split_params docker_build_callback "$@"
