# Deploying the ACN node

# Pre-requisites
- Hosted zone on aws with ports forwarded
- Kubernetes cluster
- Helm
- Kubectl
- nginx-ingress 

# To install the acn node
1. create a name space.
```bash
kubectl create ns dht-node
```
2. Install from the chart
```bash
cd acn-deployment
helm install agents-dht-test . -n dht-node
```
3. create the configuration for the ingress in the name space of the ingress controller.
```bash
kubectl apply -f ingress_tcp_routing/tcp_routing_config_map.yaml
```
4. patch in the extra ports for the ingress controller deployment.
```bash
kubectl edit -n ingress  deployment nginx-ingress-controller
```
Add in the following yaml to the ports key for the deployment spec;
```yaml
        - containerPort: 9004
          hostPort: 9004
          name: acn-2
          protocol: TCP
        - containerPort: 9003
          hostPort: 9003
          name: acn-1
          protocol: TCP
```
Add in the following yaml to the deployment container start args
```yaml
        - --tcp-services-configmap=ingress/tcp-services
```
so that the -args flag looks like so;
```yaml
    spec:
      containers:
      - args:
        - /nginx-ingress-controller
        - --ingress-class=public
        - --tcp-services-configmap=ingress/tcp-services
```

## Building and pushing images.
```bash
skaffold build
```
