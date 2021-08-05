## Minikube setup 

At the point of running command `helm install agents-dht-test .` which is in 4a at scripts/acn/README.md, there are some setup needed on minikube to support this project

# 1.Metallb 
Refer to installation tab on: https://metallb.universe.tf/

After installation of metallb in configuration tab, layer 2 configuration, create a configmap with your minikube subnet

# 2.Instio
Refer to installation on: https://instio.io/

In documentation tab, click setup then getting started which will show how to download istio in the minikube cluster. In the instioctl command part, notice you need to change the profile from demo to default

3. To resolve error with DNSEndpoint in `helm install agents-dht-test .` change `enable=true` to `enabled=false` in /scripts/acn/helm-chart/values.yaml line 4 gateway and virtual service will be created automatically by helm

4. It is useful to run `minikube ip` to test connectivity and also for metallb configuration to replace the ip subnet with that of minikube