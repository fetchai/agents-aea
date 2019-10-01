# Docker Deployment image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

We recommend using the following command for building:

    ./deploy-image/scripts/docker-build-img.sh -t aea-deploy:latest -- 
    

To pass immediate parameters to the `docker build` command:

    ./deploy-image/scripts/docker-build-img.sh arg1 arg2 --    

E.g.:

    ./deploy-image/scripts/docker-build-img.sh --squash --cpus 4 --compress --    


## Run

    docker run -it aea-develop:latest 
 
