# Docker User image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

We recommend using the following command for building:

    docker build . \
    -t valory/open-aea-user:latest \
    --file user-image/Dockerfile 


## Publish
     docker push valory/open-aea-user:latest
