
# Deploying a benchmark run:

First remove any old config maps and create a new one:
``` bash
kubectl delete configmap run-benchmark
kubectl create configmap run-benchmark --from-file=run_benchmark.sh
```

To remove old nodes (auto-restarts new node):

``` bash
kubectl delete pod NODE_NAME
```

To access nginx you will need something like:
``` bash
kubectl port-forward NODE_NAME 8000:80
```
then
``` bash
curl localhost:8000
```