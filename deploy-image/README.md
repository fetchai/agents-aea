# Docker Deployment image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

We recommend using the following command for building:

    ./deploy-image/scripts/docker-build-img.sh \
        -t aea-deploy:latest --

## Run

    docker run --env AGENT_REPO_URL=https://github.com/fetchai/echo_agent.git aea-deploy:latest

## Publish

First, be sure you tagged the image with the `latest` tag: 

    docker tag aea-deploy:<latest-version-number> aea-deploy:latest

Then, publish the images. First, the `aea-deploy:<latest-version-number>`

    ./develop-image/scripts/docker-publish-img.sh

And then, the `aea-deploy:latest` image:

- In `docker-env.sh`, uncomment `DOCKER_IMAGE_TAG=aea-deploy:latest`  

- Run the publish command again: 

      ./develop-image/scripts/docker-publish-img.sh


## TODO
We need to add support for setting the connection endpoints for OEF/Ledger so they can be used a deploytime. I would suggest these are set as environment variables if possible.
