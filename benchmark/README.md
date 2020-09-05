
# Running a benchmark locally:

First, set permissions:
``` bash
chmod +x /benchmark/checks/run_benchmark.sh
```

Then, run:
``` bash
./benchmark/checks/run_benchmark.sh
```
or to save to file:

``` bash
./benchmark/checks/run_benchmark.sh | tee benchmark.txt
```

The benchmark will use the locally installed aea version!


# Deploying a benchmark run and serving results:

First remove any old config maps and create a new one:
``` bash
kubectl delete configmap run-benchmark
kubectl create configmap run-benchmark --from-file=run_from_branch.sh
```

To remove old nodes (auto-restarts new node):

``` bash
kubectl delete pod NODE_NAME
```

To completely remove:

``` bash
kubectl delete deployment benchmark
```

To deploy:

``` bash
kubectl apply -f benchmark-deployment.yaml
```

List pods:

``` bash
kubectl get pod -o wide
```

To access nginx (wait for status: ` `):
``` bash
kubectl port-forward NODE_NAME 8000:80
```
then
``` bash
curl localhost:8000
```