The `fetchai/p2p_libp2p:0.6.0` connection allows AEAs to create a peer-to-peer communication network. In particular, the connection creates an overlay network which maps agents' public keys to IP addresses.

## Local demo

### Create and run the genesis AEA

Create one AEA as follows:

``` bash
aea create my_genesis_aea
cd my_genesis_aea
aea add connection fetchai/p2p_libp2p:0.6.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.6.0
aea run --connections fetchai/p2p_libp2p:0.6.0
```

### Create and run another AEA

Create a second AEA:

``` bash
aea create my_other_aea
cd my_other_aea
aea add connection fetchai/p2p_libp2p:0.6.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.6.0
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
aea run --connections fetchai/p2p_libp2p:0.6.0
```

You can inspect the `libp2p_node.log` log files of the AEA to see how they discover each other.


## Local demo with skills

Explore the <a href="../weather-skills">demo section</a> for further examples.

## Deployed agent communication network

You can connect to the deployed public test network by adding one or multiple of the following addresses as the `libp2p_entry_peers`:

```yaml
/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx
/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW
/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9002/p2p/16Uiu2HAmNJ8ZPRaXgYjhFf8xo8RBTX8YoUU5kzTW7Z4E5J3x9L1t
```

In particular, by modifying the configuration such that:
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: [/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx, /dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW, /dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9002/p2p/16Uiu2HAmNJ8ZPRaXgYjhFf8xo8RBTX8YoUU5kzTW7Z4E5J3x9L1t]
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
```
