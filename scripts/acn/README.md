# Installing the agent communication network (ACN) in Kubernetes using helm

**Requirements:** `helm` needs to be installed.

`helm` provides a quick way of installing and updating existing ACN deployments.

**NOTE:** Please use the provided `values.yaml` file only for deploying test networks as it includes private keys.

To deploy a test network do the following steps:

1. Build and upload the ACN node image by running `./build_upload_img.sh`. You have to execute this from this folder.
2. update the image tag (two instances) in the `helm-chart/values.yaml`
3. `cd helm-chart`

**NOTE: Make sure to be in the `agents-p2p-dht-testnet` namespace before proceeding**

4. a) If this is the first time deploying run `helm install agents-dht-test .`
   b) If you are upgrading an existing installation (see if there is one by `helm ls`) run `helm upgrade agents-dht-test .`

## Simple image update:

Run `./build_upload_img.sh` and take note of the image tag.

Replace below `IMAGE_TAG_HERE` with the image tag.
``` bash
kubens agents-p2p-dht-testnet
kubectl set image sts/acn-node-9005 acn-node=gcr.io/fetch-ai-colearn/acn_node:{IMAGE_TAG_HERE}
kubectl set image sts/acn-node-9003 acn-node=gcr.io/fetch-ai-colearn/acn_node:{IMAGE_TAG_HERE}
kubectl set image sts/acn-node-9004 acn-node=gcr.io/fetch-ai-colearn/acn_node:{IMAGE_TAG_HERE}

kubens agents-p2p-dht
kubectl set image sts/acn-node-9002 acn-node=gcr.io/fetch-ai-colearn/acn_node:{IMAGE_TAG_HERE}
kubectl set image sts/acn-node-9000 acn-node=gcr.io/fetch-ai-colearn/acn_node:{IMAGE_TAG_HERE}
kubectl set image sts/acn-node-9001 acn-node=gcr.io/fetch-ai-colearn/acn_node:{IMAGE_TAG_HERE}
```

# The agent communication network (ACN) Kubernetes deployment script

The `k8s_deploy_acn_node.py` script provides a configurable, reproducible, and verifiable deployment of the ACN node to a Kubernetes cluster.
Configuration of the ACN node, docker image, and Kubernetes is passed through command-line interface. The script will then verify it, generate the
corresponding YAML deployment file and finally deploy it. 
The script can also delete a deployment by appending `--delete` to the CLI arguments used to create the deployment.

The generated YAML deployment file includes:
- a `statefulSet` to persist ACN node log file across runs
- a service for restarting the node (pod) in case of failure
- a `DNSEndpoint` to expose public port
- a secret to safely upload the node's private key 

The generated YAML deployment file can be saved for future re-deployments by using CLI option `--from-file`. 
Options `--from-file` and `--delete` can be combined as quick way to delete a previous deployment from Kubernetes cluster.
Option `--generate-only` can be used to generate the deployment file without submitting it to the cluster.

To reduce the number of CLI arguments to pass, the script offers defaults for docker and Kubernetes configuration
that can be used by setting `--k8s-fetchai-defaults`, `--docker-fetchai-defaults` or `--docker-fetchai-defaults-dev`.

## Usage examples


- deploy a node using CLI options
  ```bash
  python3 scripts/acn/k8s_deploy_acn_node.py --acn-key-file fet_key_test_1.txt --acn-port 9009 --acn-port-delegate 11009 --k8s-fetchai-defaults --docker-fetchai-defaults-dev
  ```

- delete deployment using CLI options
  ```bash
  python3 scripts/acn/k8s_deploy_acn_node.py --acn-key-file fet_key_test_1.txt --acn-port 9009 --acn-port-delegate 11009 --k8s-fetchai-defaults --docker-fetchai-defaults-dev --delete
  ```

- redeploy using the generated deployment file
  ```bash
  python3 scripts/acn/k8s_deploy_acn_node.py --from-file .acn_deployment.yaml
  ```

- delete deployment using the generated deployment file
  ```bash
  python3 scripts/acn/k8s_deploy_acn_node.py  --from-file .acn_deployment.yaml --delete
  ```

