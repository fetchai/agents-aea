# Docker Deployment image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

We recommend using the following command for building:

    ./deploy-image/scripts/docker-build-img.sh -t fetchai/aea-deploy:latest --

## Run

    docker run --env AGENT_REPO_URL=https://github.com/fetchai/echo_agent.git aea-deploy:latest

This will run the `entrypoint.sh` script inside the deployment container.

Or, you can try a dry run without setting `AGENT_REPO_URL` (it will build an echo agent):

    docker run -it fetchai/aea-deploy:latest

To run a bash shell inside the container: 

    docker run -it fetchai/aea-deploy:latest bash

## Publish

First, be sure you tagged the image with the `latest` tag: 

    docker tag fetchai/aea-deploy:<latest-version-number> fetchai/aea-deploy:latest

Then, publish the images. First, the `fetchai/aea-deploy:<latest-version-number>`

    ./develop-image/scripts/docker-publish-img.sh

And then, the `fetchai/aea-deploy:latest` image:

- In `docker-env.sh`, uncomment `DOCKER_IMAGE_TAG=fetchai/aea-deploy:latest`  

- Run the publish command again: 

      ./develop-image/scripts/docker-publish-img.sh


## TODO
We need to add support for setting the connection endpoints for OEF/Ledger so they can be used a deploy time. I would suggest these are set as environment variables if possible.
