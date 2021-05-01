# Tac Deployment image


### Build the image

``` bash
docker build -t tac-deploy -f Dockerfile .
```
### Configure
add preferred amount of tac participants agents
```
PARTICIPANTS_AMOUNT=5
```
to `.env` file

### Run locally

``` bash
docker run --env-file .env -v "$(pwd)/data:/data" -ti tac-deploy
```


### Run in the cloud
GCloud should be configured first!

tag it first
``` bash
docker image tag tac-deploy gcr.io/fetch-ai-sandbox/tac_deploy:0.0.3
```


push it to remote repo
``` bash
docker push gcr.io/fetch-ai-sandbox/tac_deploy:0.0.3
```

run it
``` bash
kubectl run tac-deploy-test --image=gcr.io/fetch-ai-sandbox/tac_deploy:0.0.3 --env="PARTICIPANTS_AMOUNT=5" --attach
```

access the container
run it
``` bash
kubectl exec tac-deploy-test -ti -- /bin/sh
cd /data
ls -1
```


stop it
``` bash
kubectl delete pod tac-deploy-test
```



deploy:
push image first!
``` bash
kubectl apply -f ./tac-deployment.yaml
```

get pods list
``` bash
kubectl get pods
```

fetch logs
``` bash
kubectl cp tac-deploy-SOMETHING:/data ./output_dir
```

delete deployment
``` bash
kubectl delete deployment tac-deploy
```