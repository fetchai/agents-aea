The `fetchai/p2p_libp2p:0.11.0` connection allows AEAs to create a peer-to-peer communication network. In particular, the connection creates an overlay network which maps agents' public keys to IP addresses.

## Local demo

### Create and run the genesis AEA

Create one AEA as follows:

``` bash
aea create my_genesis_aea
cd my_genesis_aea
aea add connection fetchai/p2p_libp2p:0.11.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.11.0
aea run --connections fetchai/p2p_libp2p:0.11.0
```

### Create and run another AEA

Create a second AEA:

``` bash
aea create my_other_aea
cd my_other_aea
aea add connection fetchai/p2p_libp2p:0.11.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.11.0
```

Provide the AEA with the information it needs to find the genesis by replacing the following block in `vendor/fetchai/connnections/p2p_libp2p/connection.yaml`:

``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: MULTI_ADDRESSES
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
Here `MULTI_ADDRESSES` needs to be replaced with the list of multi addresses displayed in the log output of the genesis AEA.

Run the AEA:

``` bash
aea run --connections fetchai/p2p_libp2p:0.11.0
```

You can inspect the `libp2p_node.log` log files of the AEA to see how they discover each other.


## Local demo with skills

Explore the <a href="../weather-skills">demo section</a> for further examples.

## Deployed agent communication network

You can connect to the deployed public test network by adding one or multiple of the following addresses as the `libp2p_entry_peers`:

```yaml
/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx
/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW
```

In particular, by modifying the configuration such that:
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: [/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx,/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW]
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
```

## Configuring the `connection.yaml` entries:


To learn more about how to configure your `fetchai/p2p_libp2p:0.11.0` connection consult the `README.md` supplied with the connection package.

## Running Go peer standalone

You can run the peer node in standalone mode, that is, as a Go process with no dependency to the agents framework. 
To facilitate the deployment, we provide a script
 <a href="https://github.com/fetchai/agents-aea/blob/master/scripts/acn/run_acn_node_standalone.py" target="_blank">`run_acn_node_standalone.py`</a>
 and a corresponding 
 <a href="https://github.com/fetchai/agents-aea/blob/master/scripts/acn/Dockerfile" target="_blank">Dockerfile</a>.

First, you need to build the node's binary (`libp2p_node`) either:

- locally
  ``` bash
  svn export https://github.com/fetchai/agents-aea.git/trunk/packages/fetchai/connections/p2p_libp2p
  cd p2p_libp2p
  go build
  chmod +x libp2p_node
  ```
  Make sure you satisfy the <a href="../quickstart">system requirements</a>.
- or within a docker image using the provided Dockerfile
  ``` bash
  docker build -t acn_node_standalone -f scripts/acn/Dockerfile .
  ```

Next, to run the node binary in standalone mode, it requires values for the following entries:

- `AEA_P2P_ID`: the node's private key, will be used as its identity
- `AEA_P2P_URI`: the local host and port to use by node
- `AEA_P2P_URI_PUBLIC`: the URI under which the peer is reachable publicly
- `AEA_P2P_DELEGATE_URI`: the URI under which the peer receives delegate connections
- `AEA_P2P_ENTRY_URIS`: an optionally supplied list of entry Multiaddresses for the peer to bootstrap, comma-separated (`,`)

The script allows different methods to pass these values to the node:

- as environment variables exported in format `<ENTRY_KEYWORD>=<ENTRY_VALUE>` for each entry
  ``` bash
  python3 run_acn_node_standalone.py libp2p_node --config-from-env
  ```
- using an environment file containing the entries and their values in format `<ENTRY_KEYWORD>=<ENTRY_VALUE>`, one per line
  ``` bash
  python3 run_acn_node_standalone.py libp2p_node --config-from-file <env-file-path>
  ```
  or
  ``` bash
  docker run -v <acn_config_file>:/acn/acn_config -it acn_node_standalone --config-from-file /acn/acn_config
  ```
- using command line arguments as follow
  ``` bash
  python3 run_acn_node_standalone.py libp2p_node --key-file <node_private_key.txt> \
    --uri <AEA_P2P_URI> --uri-external <AEA_P2P_URI_PUBLIC>  \
    --uri-delegate <AEA_P2P_DELEGATE_URI> \
    --entry-peers-maddrs <AEA_P2P_ENTRY_URI_1> <AEA_P2P_ENTRY_URI_2> ...
  ```
  or 
  ``` bash
  docker run -v <node_private_key.txt>:/acn/key.txt -it acn_node_standalone --key-file /acn/key.txt \
    --uri <AEA_P2P_URI> --uri-external <AEA_P2P_URI_PUBLIC>  \
    --uri-delegate <AEA_P2P_DELEGATE_URI> \
    --entry-peers-maddrs <AEA_P2P_ENTRY_URI_1> <AEA_P2P_ENTRY_URI_2> ...
  ```

Note that the script will always save the configuration of the running node as a file under name `.acn_config` within current working directory. This can be handy to ensure exact same configuration for future runs of the node.