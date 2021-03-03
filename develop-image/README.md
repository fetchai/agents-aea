# Docker Development image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

    ./develop-image/scripts/docker-build-img.sh -t fetchai/aea-deploy:latest --
    

To pass immediate parameters to the `docker build` command:

    ./develop-image/scripts/docker-build-img.sh arg1 arg2 --    

E.g.:

    ./develop-image/scripts/docker-build-img.sh --squash --cpus 4 --compress --    


## Run

    ./develop-image/scripts/docker-run.sh -- /bin/bash
 
As before, to pass parameters to the `docker run` command:

    ./develop-image/scripts/docker-run.sh -p 8080:80 -- /bin/bash


## Publish

First, be sure you tagged the image with the `latest` tag: 

    docker tag fetchai/aea-develop:<latest-version-number> fetchai/aea-develop:latest

Then, publish the images. First, the `fetchai/aea-develop:<latest-version-number>`

    ./develop-image/scripts/docker-publish-img.sh

And then, the `fetchai/aea-develop:latest` image:

- In `docker-env.sh`, uncomment `DOCKER_IMAGE_TAG=fetchai/aea-develop:latest`  

- Run the publish command again: 

      ./develop-image/scripts/docker-publish-img.sh

# Publish to k8s

Switch the context:
``` bash
kubectx sandbox
```

List pods in cluster:
``` bash
kubectl get pods
```

Optionally, create new namespace:
``` bash
kubectl create namespace aea-research
```

Ensure right namespace is used:
``` bash
kubens aea-research
```
Choose namespace in cluster:
``` bash
kubens aea-research
```
To enter selected namespace:
``` bash
kubens
```

From the `develop-image` folder run:
``` bash
skaffold run -p sandbox
```

SSH into a new image:
``` bash
kubectl run --generator=run-pod/v1 -it debian --image=debian -- bash
```

# Dedicated node pool for benchmarking agents


## Setup and tear down

To create the node pool
``` bash
gcloud container node-pools create agent-test-pool --cluster sandbox --project fetch-ai-sandbox --node-taints dedicated=agent:NoSchedule --machine-type=n1-standard-4 --num-nodes=1 --enable-autoscaling --node-labels=type=agent-test --max-nodes=1  --min-nodes=0
```
To remove the node pool 
``` bash
gcloud container node-pools delete agent-test-pool --cluster sandbox --project fetch-ai-sandbox
```

## Usage

List pods

``` bash
kubectl get pod -o wide
```

``` bash
kubectl exec -it NAME -- bash
```



