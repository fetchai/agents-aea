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

# Publish to k8s

Switch the context:
```
kubectx sandbox
```

List pods in cluster:
```
kubectl get pods
```

Optionally, create new namespace:
```
kubectl create namespace aea-research
```

Ensure right namespace is used:
```
kubens aea-research
```
Choose namespace in cluster:
```
kubens aea-research
```
To enter selected namespace:
```
kubens
```

From the `develop-image` folder run:
```
skaffold run -p sandbox
```

SSH into a new image:
```
kubectl run --generator=run-pod/v1 -it debian --image=debian -- bash
```