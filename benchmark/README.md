How to create teh configmap?
`kubectl delete configmap run-benchmark`
`kubectl create configmap run-benchmark --from-file=run_benchmark.sh`