``` bash
{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["REPLACE_WITH_MULTI_ADDRESS_HERE"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}
```

``` bash
aea fetch fetchai/thermometer_aea:0.30.5 --alias my_thermometer_aea
cd my_thermometer_aea
aea install
aea build
```

``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/p2p_libp2p:0.27.5
aea add connection fetchai/soef:0.27.6
aea add connection fetchai/ledger:0.21.5
aea add skill fetchai/thermometer:0.27.6
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.27.5
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.1.7": "fetchai/ledger:0.21.5",
  "fetchai/oef_search:1.1.7": "fetchai/soef:0.27.6"
}'
```

``` bash
aea fetch fetchai/thermometer_client:0.32.5 --alias my_thermometer_client
cd my_thermometer_client
aea install
aea build
```

``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/p2p_libp2p:0.27.5
aea add connection fetchai/soef:0.27.6
aea add connection fetchai/ledger:0.21.5
aea add skill fetchai/thermometer_client:0.26.6
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.27.5
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.1.7": "fetchai/ledger:0.21.5",
  "fetchai/oef_search:1.1.7": "fetchai/soef:0.27.6"
}'
```

``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

``` bash
aea issue-certificates
```

``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
```

``` bash
aea generate-wealth fetchai
```

``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

``` bash
aea issue-certificates
```

``` bash
aea run
```

``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}'
```

``` bash
aea run
```

``` bash
cd ..
aea delete my_thermometer_aea
aea delete my_thermometer_client
```

``` yaml
---
public_id: fetchai/p2p_libp2p:0.27.5
type: connection
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers:
  - SOME_ADDRESS
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
