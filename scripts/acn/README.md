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
  python3 scripts/acn/k8s_deploy_acn_node.py --acn-key-file fet_key_test_1.txt --acn-port 9009 --acn-port-delegate 11009 --acn-port-monitoring 8080 --k8s-fetchai-defaults --docker-fetchai-defaults-dev
  ```

- delete deployment using cli options
  ```bash
  python3 scripts/acn/k8s_deploy_acn_node.py --acn-key-file fet_key_test_1.txt --acn-port 9009 --acn-port-delegate 11009 --acn-port-monitoring 8080 --k8s-fetchai-defaults --docker-fetchai-defaults-dev --delete
  ```

- redeploy using the generated deployment file
  ```bash
  python3 scripts/acn/k8s_deploy_acn_node.py --from-file .acn_deployment.yaml
  ```

- delete deployment using the generated deployment file
  ```bash
  python3 scripts/acn/k8s_deploy_acn_node.py  --from-file .acn_deployment.yaml --delete
  ```

