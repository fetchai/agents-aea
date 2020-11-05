# Docker User image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

We recommend using the following command for building:

    ./user-image/scripts/docker-build-img.sh -t fetchai/aea-user:latest --

## Publish

First,

    ./user-image/scripts/docker-publish-img.sh

And then, in `docker-env.sh`, uncomment `DOCKER_IMAGE_TAG=aea-user:latest` and comment the alternative line, then run the publish command again: 

    ./user-image/scripts/docker-publish-img.sh
