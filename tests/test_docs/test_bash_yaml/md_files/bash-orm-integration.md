``` bash
aea fetch fetchai/thermometer_aea:0.29.0 --alias my_thermometer_aea
cd my_thermometer_aea
aea install
aea build
```
``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/thermometer:0.26.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea install
aea build
```
``` bash
aea fetch fetchai/thermometer_client:0.30.0 --alias my_thermometer_client
cd my_thermometer_client
aea install
aea build
```
``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/thermometer_client:0.25.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea install
aea build
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
```
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
```
``` bash
aea generate-wealth fetchai
```
``` bash
aea install
aea build
```
``` bash
aea eject skill fetchai/thermometer:0.26.0
```
``` bash
aea fingerprint skill {YOUR_AUTHOR_HANDLE}/thermometer:0.1.0
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
models:
  ...
  strategy:
    args:
      currency_id: FET
      data_for_sale:
        temperature: 26
      has_data_source: false
      is_ledger_tx: true
      ledger_id: fetchai
      location:
        latitude: 51.5194
        longitude: 0.127
      service_data:
        key: seller_service
        value: thermometer_data
      service_id: thermometer_data
      unit_price: 10
    class_name: Strategy
dependencies:
  SQLAlchemy: {}
```
``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      is_ledger_tx: true
      ledger_id: fetchai
      location:
        latitude: 51.5194
        longitude: 0.127
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      search_query:
        constraint_type: ==
        search_key: seller_service
        search_value: thermometer_data
      search_radius: 5.0
      service_id: thermometer_data
    class_name: Strategy
```
``` yaml
---
public_id: fetchai/p2p_libp2p:0.25.0
type: connection
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers:
  - SOME_ADDRESS
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```