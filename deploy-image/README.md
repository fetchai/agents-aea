# Docker Deployment image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

We recommend using the following command for building:

    ./deploy-image/scripts/docker-build-img.sh \
        -t aea-deploy:latest --

## Run

    docker run --env AGENT_REPO_URL=https://github.com/fetchai/echo_agent.git aea-deploy:latest

## TODO
We need to add support for setting the connection endpoints for OEF/Ledger so they can be used a deploytime. I would suggest these are set as environment variables if possible.
