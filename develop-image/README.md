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
