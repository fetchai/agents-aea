``` bash
aea fetch fetchai/ml_data_provider:0.9.0
cd ml_data_provider
aea install
``` 
``` bash
aea create ml_data_provider
cd ml_data_provider
aea add connection fetchai/p2p_libp2p:0.6.0
aea add connection fetchai/soef:0.6.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/ml_data_provider:0.7.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.6.0
aea install
```
``` bash
aea fetch fetchai/ml_model_trainer:0.9.0
cd ml_model_trainer
aea install
```
``` bash
aea create ml_model_trainer
cd ml_model_trainer
aea add connection fetchai/p2p_libp2p:0.6.0
aea add connection fetchai/soef:0.6.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/ml_train:0.7.0
aea config set agent.default_connection fetchai/p2p_libp2p:0.6.0
aea install
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea generate-wealth cosmos
```
``` bash
aea run
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
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.2.0
  fetchai/oef_search:0.3.0: fetchai/soef:0.6.0
```
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.2.0
  fetchai/oef_search:0.3.0: fetchai/soef:0.6.0
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
