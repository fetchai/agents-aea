# Docker Development image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

    ./develop-image/scripts/docker-build-img.sh
    

To pass immediate parameters to the `docker build` command:

    ./develop-image/scripts/docker-build-img.sh arg1 arg2 --    

E.g.:

    ./develop-image/scripts/docker-build-img.sh --squash --cpus 4 --compress --    


## Run

    ./develop-image/scripts/docker-run.sh -- /bin/bash
 
As before, to pass params to the `docker run` command:

    ./develop-image/scripts/docker-run.sh -p 8080:80 -- /bin/bash


## Publish

First, be sure you tagged the image with the `latest` tag: 

    docker tag aea-develop:<latest-version-number> aea-develop:latest

Then, publish the images. First, the `aea-develop:<latest-version-number>`

    ./develop-image/scripts/docker-publish-img.sh

And then, the `aea-develop:latest` image:

- In `docker-env.sh`, uncomment `DOCKER_IMAGE_TAG=aea-develop:latest`  

- Run the publish command again: 

      ./develop-image/scripts/docker-publish-img.sh
