``` bash
aea fetch fetchai/car_detector:0.21.0
cd car_detector
aea install
aea build
```
``` bash
aea create car_detector
cd car_detector
aea add connection fetchai/p2p_libp2p:0.15.0
aea add connection fetchai/soef:0.16.0
aea add connection fetchai/ledger:0.13.0
aea add skill fetchai/carpark_detection:0.19.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.15.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:0.10.0": "fetchai/ledger:0.13.0",
  "fetchai/oef_search:0.13.0": "fetchai/soef:0.16.0"
}'
```
``` bash
aea fetch fetchai/car_data_buyer:0.22.0
cd car_data_buyer
aea install
aea build
```
``` bash
aea create car_data_buyer
cd car_data_buyer
aea add connection fetchai/p2p_libp2p:0.15.0
aea add connection fetchai/soef:0.16.0
aea add connection fetchai/ledger:0.13.0
aea add skill fetchai/carpark_client:0.20.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.15.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:0.10.0": "fetchai/ledger:0.13.0",
  "fetchai/oef_search:0.13.0": "fetchai/soef:0.16.0"
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
aea delete car_detector
aea delete car_data_buyer
```
``` yaml
---
public_id: fetchai/p2p_libp2p:0.15.0
type: connection
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers:
  - SOME_ADDRESS
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```