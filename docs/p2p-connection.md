The `fetchai/p2p_libp2p:0.5.0` connection allows AEAs to create a peer-to-peer communication network. In particular, the connection creates an overlay network which maps agents' public keys to IP addresses.

## Local demo

### Create and run the genesis AEA

Create one AEA as follows:

``` bash
aea create my_genesis_aea
cd my_genesis_aea
aea add connection fetchai/p2p_libp2p:0.5.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.5.0
aea run --connections fetchai/p2p_libp2p:0.5.0
```

### Create and run another AEA

Create a second AEA:

``` bash
aea create my_other_aea
cd my_other_aea
aea add connection fetchai/p2p_libp2p:0.5.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.5.0
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
aea run --connections fetchai/p2p_libp2p:0.5.0
```

You can inspect the `libp2p_node.log` log files of the AEA to see how they discover each other.


## Local demo with skills

### Fetch the weather station and client

Create one AEA as follows:

``` bash
aea fetch fetchai/weather_station:0.8.0
aea fetch fetchai/weather_client:0.8.0
```

Then enter each project individually and execute the following to add the `p2p_libp2p` connection:
``` bash
aea add connection fetchai/p2p_libp2p:0.5.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.5.0
```

Then extend the `aea-config.yaml` of each project as follows:
``` yaml
default_routing:
  ? "fetchai/oef_search:0.3.0"
  : "fetchai/oef:0.6.0"
```
### Run OEF

Run the oef for search and discovery:
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

### Run weather station

Run the weather station first:
``` bash
aea run --connections "fetchai/p2p_libp2p:0.5.0,fetchai/oef:0.6.0"
```
The weather station will form the genesis node. Wait until you see the lines:
``` bash
My libp2p addresses: ...
```
Take note of these as the genesis' `MULTI_ADDRESSES = ["{addr1}", "{addr2}"]`.

### Generate wealth for the weather client AEA

The weather client needs to have some wealth to purchase the weather station information.

First, create the private key for the weather client AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

Then, create some wealth for your weather client based on the network you want to transact with. On the Fetch.ai `testnet` network:
``` bash
aea generate-wealth fetchai
```

### Run the weather client

Provide the weather client AEA with the information it needs to find the genesis by adding the following block to `vendor/fetchai/connnections/p2p_libp2p/connection.yaml`:
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: MULTI_ADDRESSES
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
Here `MULTI_ADDRESSES` needs to be replaced with the list of multi addresses displayed in the log output of the weather station AEA.

Now run the weather client:
``` bash
aea run --connections "fetchai/p2p_libp2p:0.5.0,fetchai/oef:0.6.0"
```

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
