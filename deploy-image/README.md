# Docker Deployment image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

We recommend using the following command for building:

    ./deploy-image/scripts/docker-build-img.sh \
        -t aea-deploy:latest \
        --build-arg AGENT_REPO_URL=https://github.com/username/repo.git --
    

E.g.:

    ./deploy-image/scripts/docker-build-img.sh \
        -t aea-deploy:latest \
        --build-arg AGENT_REPO_URL=https://github.com/fetchai/echo_agent.git --    


## Run

    docker run -it aea-deploy:latest 
 
