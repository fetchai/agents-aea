``` bash
aea create my_genesis_aea
cd my_genesis_aea
aea add connection fetchai/p2p_libp2p:0.1.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.1.0
aea run --connections fetchai/p2p_libp2p:0.1.0
```
``` bash
aea create my_other_aea
cd my_other_aea
aea add connection fetchai/p2p_libp2p:0.1.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.1.0
```
``` bash
aea run --connections fetchai/p2p_libp2p:0.1.0
```
``` bash
aea fetch fetchai/weather_station:0.4.0
aea fetch fetchai/weather_client:0.4.0
```
``` bash
aea add connection fetchai/p2p_libp2p:0.1.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.1.0
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea run --connections "fetchai/p2p_libp2p:0.1.0,fetchai/oef:0.3.0"
```
``` bash
My libp2p addresses: ...
```
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```
``` bash
aea generate-wealth fetchai
```
``` bash
aea run --connections "fetchai/p2p_libp2p:0.1.0,fetchai/oef:0.3.0"
```
``` yaml
config:
  libp2p_entry_peers: MULTI_ADDRESSES
  libp2p_host: 0.0.0.0
  libp2p_log_file: libp2p_node.log
  libp2p_port: 9001
```
``` yaml
config:
  libp2p_entry_peers: MULTI_ADDRESSES
  libp2p_host: 0.0.0.0
  libp2p_log_file: libp2p_node.log
  libp2p_port: 9001
```
``` yaml
default_routing:
  ? "fetchai/oef_search:0.1.0"
  : "fetchai/oef:0.3.0"
```
```yaml
/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx
/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW
/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9002/p2p/16Uiu2HAmNJ8ZPRaXgYjhFf8xo8RBTX8YoUU5kzTW7Z4E5J3x9L1t
```
``` yaml
config:
  libp2p_entry_peers: [/dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx, /dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW, /dns4/agents-p2p-dht.sandbox.fetch-ai.com/tcp/9002/p2p/16Uiu2HAmNJ8ZPRaXgYjhFf8xo8RBTX8YoUU5kzTW7Z4E5J3x9L1t]
  libp2p_host: 0.0.0.0
  libp2p_log_file: libp2p_node.log
  libp2p_port: 9001
```