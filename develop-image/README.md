# Docker Development image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

    docker build . \
    -t valory/open-aea-develop:latest \
    --file develop-image/Dockerfile 

To pass immediate parameters to the `docker build` command:

    docker build . \
        -t valory/open-aea-develop:latest \
        --file develop-image/Dockerfile \
        arg1 arg2

E.g.:

    docker build . \
        -t valory/open-aea-develop:latest \
        --file develop-image/Dockerfile  \
        --cpu-quota 4 --compress

## Run
    docker run -it valory/open-aea-develop:latest /bin/bash
 
Pass parameters to the `docker run` command:

    docker run -it -p 8080:8080 valory/open-aea-develop:latest /bin/bash


## Publish

First, be sure you tagged the image with the `latest` tag: 

    docker tag valory/open-aea-develop:<latest-version-number> valory/open-aea-develop:latest

Then, publish the images. First, the `valory/open-aea-develop:<latest-version-number>`

    docker push valory/open-aea-develop:<latest-version-number>

And then, the `valory/open-aea-develop:latest` image:

    docker push valory/open-aea-develop:latest

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



