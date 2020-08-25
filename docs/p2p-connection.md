The `fetchai/p2p_libp2p:0.8.0` connection allows AEAs to create a peer-to-peer communication network. In particular, the connection creates an overlay network which maps agents' public keys to IP addresses.

## Local demo

### Create and run the genesis AEA

Create one AEA as follows:

``` bash
aea create my_genesis_aea
cd my_genesis_aea
aea add connection fetchai/p2p_libp2p:0.8.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.8.0
aea run --connections fetchai/p2p_libp2p:0.8.0
```

### Create and run another AEA

Create a second AEA:

``` bash
aea create my_other_aea
cd my_other_aea
aea add connection fetchai/p2p_libp2p:0.8.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.8.0
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
aea run --connections fetchai/p2p_libp2p:0.8.0
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


To learn more about how to configure your `fetchai/p2p_libp2p:0.8.0` connection consult the `README.md` supplied with the connection package.

## Running Go peer standalone

You can run the peer node only, a Go process. Make sure you satisfy the <a href="../quickstart">system requirements</a>.

First, fetch the code and enter the directory:
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages/fetchai/connections/p2p_libp2p
cd p2p_libp2p
```

Second, build the node:
``` bash
go build
```

Third, create an environment file:
``` txt
AEA_AGENT_ADDR=cosmos1azvdhesjk739d2j0xdmhyzlu3kfvqqje9r7uay
AEA_P2P_ID=1ceb61fb96132480c8a8bc3023801e626fff0f871965858584744ed5a6299773
AEA_P2P_URI=127.0.0.1:9001
AEA_P2P_ENTRY_URIS=/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAm6ghFe59TZ2vHQCcr1dx5P4WWEEAfVp5K6jcgmXjG8bGQ
NODE_TO_AEA=033a2-libp2p_to_aea
AEA_TO_NODE=033a2-aea_to_libp2p
AEA_P2P_URI_PUBLIC=127.0.0.1:9001
AEA_P2P_DELEGATE_URI=127.0.0.1:11001
```
with the values set correctly and save it as `.env.libp2p`.

The entries can be described as follow:

- `AEA_AGENT_ADDR`: the agent's address
- `AEA_P2P_ID`: the agent's private key
- `AEA_P2P_URI`: the URI under which the peer is reachable locally
- `AEA_P2P_ENTRY_URIS`: an optionally supplied list of entry URIs for the peer to bootstrap
- `NODE_TO_AEA`: the <a href="https://en.wikipedia.org/wiki/Pipeline_(Unix)" target="_blank">pipe</a> for the peer to agent comms
- `AEA_TO_NODE`: the pipe for the agent to peer comms
- `AEA_P2P_URI_PUBLIC`: the URI under which the peer is reachable publicly
- `AEA_P2P_DELEGATE_URI`: the URI under which the peer receives delegate connections

Fourth, make the build file executable:
``` bash
chmod +x libp2p_node
```

Finally, run it:
``` bash
./libp2p_node .env.libp2p
```

Note, for the peer to successfully run, the `AEA_TO_NODE` pipe must already be initialized.
