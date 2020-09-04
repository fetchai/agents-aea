How to create teh configmap?
`kubectl delete configmap run-benchmark`
`kubectl create configmap run-benchmark --from-file=run_benchmark.sh`

To access nginx you will need something like
`k port-forward benchmark-54d7685f7c-lv69h 8000:80`
then
`curl localhost:8000`