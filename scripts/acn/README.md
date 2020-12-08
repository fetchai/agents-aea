# Installing the agent communication network (acn) in kubernetes using helm

**Requirements:** `helm` needs to be installed.

`helm` provides a quick way of installing and updating existing acn deployments.

**NOTE:** Please use the provided `values.yaml` file only for deploying test networks as it includes private keys.

To deploy a test network do the following steps:

1. Build and upload the acn node image by running `./build_upload_img.sh`. You have to execute this from this folder.
2. update the image tag (two instances) in the `helm-chart/values.yaml`
3. `cd helm-chart`

**NOTE: Make sure to be in the agents-p2p-dht-testnet namespace before proceeding**

4. a) If this is the first time deploying run `helm install agents-dht-test .`
   b) If you are upgrading an existing intallation (see if there is one by `helm ls`) run `helm upgrade agents-dht-test .`

# The agent communication network (acn) kubernetes deployment script

The `k8s_deploy_acn_node.py` script provides a configurable, reproducible, and verifiable deployment of the acn node to a kubernetes cluster.
Configuration of the acn node, docker image, and kubernetes is passed through command-line interface. The script will then verify it, generate the
corresponding yaml deployment file and finally deploy it. 
The script can also delete a deployment by appending `--delete` to the cli arguments used to create the deployment.

The generated yaml deployment file includes:
- a statefulSet to persist acn node log file across runs
- a service for restarting the node (pod) in case of failure
- a DNSEndpoint to expose public port
- a secret to safely upload the node's private key 

The generated yaml deployment file can be saved for future re-deployments by using cli option `--from-file`. 
Options `--from-file` and `--delete` can be combined as quick way to delete a previous deployment from kubernetes cluster.
Option `--generate-only` can be used to generate the deployment file without submitting it to the cluster.

To reduce the number of cli arguments to pass, the script offers defaults for docker and kubnernetes configuration
that can be used by setting `--k8s-fetchai-defaults`, `--docker-fetchai-defaults` or `--docker-fetchai-defaults-dev`.

## Usage examples


- deploy a node using cli options
  ```bash
  python3 scripts/acn/k8s_deploy_acn_node.py --acn-key-file fet_key_test_1.txt --acn-port 9009 --acn-port-delegate 11009 --k8s-fetchai-defaults --docker-fetchai-defaults-dev
  ```

- delete deployment using cli options
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

