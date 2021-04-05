# Tac Deployment image


### Build the image

``` bash
docker build -t tac-deploy -f Dockerfile .
```
### Configure
add preffered amount of tac participants agents
```
PARTICIPANTS_AMOUNT=5
```
to `.env` file

### Run locally

``` bash
docker run --env-file .env -v "$(pwd)/data:/data" -t tac-deploy
```


### Run in the cloud
gcloud should be configured first!

tag it first
``` bash
docker image tag tac_deploy gcr.io/fetch-ai-sandbox/tac_deploy:0.0.0
```


push it to remote repo
``` bash
docker push gcr.io/fetch-ai-sandbox/tac_deploy:0.0.0
```

run it
``` bash
kubectl run tac-deploy-test --image=gcr.io/fetch-ai-sandbox/tac_deploy:0.0.0 --env="PARTICIPANTS_AMOUNT=5" --attach
```

access container
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



