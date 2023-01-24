# Docker Development image

All the commands must be executed from the parent directory, if not stated otherwise.

## Build

``` bash
./develop-image/scripts/docker-build-img.sh -t fetchai/aea-deploy:latest --
```

To pass immediate parameters to the `docker build` command:

``` bash
./develop-image/scripts/docker-build-img.sh arg1 arg2 --    
```

E.g.:

``` bash
./develop-image/scripts/docker-build-img.sh --squash --cpus 4 --compress --    
```

## Run

``` bash
./develop-image/scripts/docker-run.sh -- /bin/bash
```

As before, to pass parameters to the `docker run` command:

``` bash
./develop-image/scripts/docker-run.sh -p 8080:80 -- /bin/bash
```

## Publish

First, be sure you tagged the image with the `latest` tag:

``` bash
docker tag fetchai/aea-develop:<latest-version-number> fetchai/aea-develop:latest
```

Then, publish the images. First, the `fetchai/aea-develop:<latest-version-number>`

``` bash
./develop-image/scripts/docker-publish-img.sh
```

And then, the `fetchai/aea-develop:latest` image:

- In `docker-env.sh`, uncomment `DOCKER_IMAGE_TAG=fetchai/aea-develop:latest`  

- Run the publish command again:

  ``` bash
  ./develop-image/scripts/docker-publish-img.sh
  ```

### Publish to k8s

Switch the context:

``` shell
kubectx sandbox
```

List pods in cluster:

``` shell
kubectl get pods
```

Optionally, create new namespace:

``` shell
kubectl create namespace aea-research
```

Ensure right namespace is used:

``` shell
kubens aea-research
```

Choose namespace in cluster:

``` shell
kubens aea-research
```

To enter selected namespace:

``` shell
kubens
```

From the `develop-image` folder run:

``` shell
skaffold run -p sandbox
```

SSH into a new image:

``` shell
kubectl run --generator=run-pod/v1 -it debian --image=debian -- bash
```

## Dedicated node pool for benchmarking agents

### Setup and tear down

To create the node pool

``` shell
gcloud container node-pools create agent-test-pool --cluster sandbox --project fetch-ai-sandbox --node-taints dedicated=agent:NoSchedule --machine-type=n1-standard-4 --num-nodes=1 --enable-autoscaling --node-labels=type=agent-test --max-nodes=1  --min-nodes=0
```

To remove the node pool

``` shell
gcloud container node-pools delete agent-test-pool --cluster sandbox --project fetch-ai-sandbox
```

### Usage

List pods

``` shell
kubectl get pod -o wide
```

``` shell
kubectl exec -it NAME -- bash
```
