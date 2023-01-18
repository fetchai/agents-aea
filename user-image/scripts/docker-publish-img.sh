#!/bin/bash -e
# NOTE: First docker needs to be authorized to push image to container registry.
#       Normally this is done using 'docker login <registrey_url>', where the
#       'registry_url' value is set in the $DOCKER_CONTAINER_REGISTRY environment
#       variable which is defined in the 'docker-env-common.sh' script file.
#       If you are using the Google cloud docker registry, please run the
#       'gcloud auth configure-docker' instead.

SCRIPTS_DIR=${0%/*}
. "$SCRIPTS_DIR"/docker-env-common.sh

docker tag "$DOCKER_IMAGE_TAG" "$REGISTRY_DOCKER_IMAGE_TAG"
docker push "$REGISTRY_DOCKER_IMAGE_TAG"
