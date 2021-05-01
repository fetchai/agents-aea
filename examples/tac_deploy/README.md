# Tac Deployment image

The TAC deployment deploys one controller and `n` tac participants.

### Build the image

To build the image:
``` bash
docker build -t tac-deploy -f Dockerfile . --no-cache
```

## Run locally

Add preferred amount of tac participants agents to `.env` file:
```
PARTICIPANTS_AMOUNT=5
```

Run:
``` bash
docker run --env-file .env -v "$(pwd)/data:/data" -ti tac-deploy
```

## Run in the cloud

GCloud should be configured first!

### Push image

Tag the image first with the latest tag:
``` bash
docker image tag tac-deploy gcr.io/fetch-ai-sandbox/tac_deploy:0.0.7
```

Push it to remote repo:
``` bash
docker push gcr.io/fetch-ai-sandbox/tac_deploy:0.0.7
```

### Run it manually

Run it
``` bash
kubectl run tac-deploy-{SOMETHING} --image=gcr.io/fetch-ai-sandbox/tac_deploy:0.0.7 --env="PARTICIPANTS_AMOUNT=5" --attach
```

Or simply restart existing deployment and latest image will be used with default configs (see below):
``` bash
kubectl delete pod tac-deploy-{SOMETHING}
```

### Manipulate container

To access the container run:
``` bash
kubectl exec tac-deploy-{SOMETHING} -ti -- /bin/sh
```

To remove all logs and all keys:
``` bash
cd ../../data
find . -name \*.log -type f -delete
find . -name \*.txt -type f -delete
```

### Full deployment:

First, push the latest image, as per above.

Second, update the `tac-deployment.yaml` file and then run:
``` bash
kubectl apply -f ./tac-deployment.yaml
```

Check for pods list:
``` bash
kubectl get pods
```

To fetch logs:
``` bash
kubectl cp tac-deploy-{SOMETHING}:/data ./output_dir
```

To delete deployment:
``` bash
kubectl delete deployment tac-deploy
```

### Analysing Logs:

Handy commands to analyse logs:
``` bash
grep -rl 'TAKE CARE! Circumventing controller identity check!' output_dir/ | sort
grep -rl 'TAKE CARE! Circumventing controller identity check!' output_dir/ | wc -l
grep -rnw 'SOEF Network Connection Error' output_dir/ |  wc -l
grep -rnw 'SOEF Server Bad Response Error' output_dir/ |  wc -l
grep -rnw 'Failure during pipe closing.' output_dir/ |  wc -l
grep -rnw 'Exception' output_dir/ |  wc -l
grep -rnw 'connect to libp2p process within timeout' output_dir/ |  wc -l
grep -rnw 'handling valid transaction' output_dir/tac_controller/ | wc -l
grep -rnw 'received invalid tac message' output_dir/tac_controller/ | wc -l
```
