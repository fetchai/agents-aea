``` bash
aea fetch fetchai/ml_data_provider:0.23.0
cd ml_data_provider
aea install
aea build
``` 
``` bash
aea create ml_data_provider
cd ml_data_provider
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/ml_data_provider:0.20.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0",
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
}'
aea install
aea build
```
``` bash
aea fetch fetchai/ml_model_trainer:0.24.0
cd ml_model_trainer
aea install
aea build
```
``` bash
aea create ml_model_trainer
cd ml_model_trainer
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/ml_train:0.22.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0",
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
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
aea delete ml_data_provider
aea delete ml_model_trainer
```
``` yaml
---
public_id: fetchai/p2p_libp2p:0.17.0
type: connection
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers:
  - SOME_ADDRESS
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```