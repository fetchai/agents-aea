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
aea fetch fetchai/ml_data_provider:0.32.1
cd ml_data_provider
aea install
aea build
``` 
``` bash
aea create ml_data_provider
cd ml_data_provider
aea add connection fetchai/p2p_libp2p:0.27.1
aea add connection fetchai/soef:0.27.2
aea add connection fetchai/ledger:0.21.1
aea add skill fetchai/ml_data_provider:0.27.2
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.27.1
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.1.2": "fetchai/ledger:0.21.1",
  "fetchai/oef_search:1.1.2": "fetchai/soef:0.27.2"
}'
aea install
aea build
```
``` bash
aea fetch fetchai/ml_model_trainer:0.33.1
cd ml_model_trainer
aea install
aea build
```
``` bash
aea create ml_model_trainer
cd ml_model_trainer
aea add connection fetchai/p2p_libp2p:0.27.1
aea add connection fetchai/soef:0.27.2
aea add connection fetchai/ledger:0.21.1
aea add skill fetchai/ml_train:0.29.2
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.27.1
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.1.2": "fetchai/ledger:0.21.1",
  "fetchai/oef_search:1.1.2": "fetchai/soef:0.27.2"
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
public_id: fetchai/p2p_libp2p:0.27.1
type: connection
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers:
  - SOME_ADDRESS
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```