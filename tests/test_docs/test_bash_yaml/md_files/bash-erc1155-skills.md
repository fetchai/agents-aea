``` bash
aea fetch fetchai/erc1155_deployer:0.17.0
cd erc1155_deployer
aea install
```
``` bash
aea create erc1155_deployer
cd erc1155_deployer
aea add connection fetchai/p2p_libp2p:0.12.0
aea add connection fetchai/soef:0.12.0
aea add connection fetchai/ledger:0.9.0
aea add skill fetchai/erc1155_deploy:0.17.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.12.0
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea fetch fetchai/erc1155_client:0.17.0
cd erc1155_client
aea install
```
``` bash
aea create erc1155_client
cd erc1155_client
aea add connection fetchai/p2p_libp2p:0.12.0
aea add connection fetchai/soef:0.12.0
aea add connection fetchai/ledger:0.9.0
aea add skill fetchai/erc1155_client:0.16.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.12.0
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea generate-wealth ethereum
```
``` bash
aea get-wealth ethereum
```
``` bash
aea config set vendor.fetchai.connections.soef.config.chain_identifier ethereum
```
``` bash
aea run
```
``` bash
registering service on SOEF.
```
``` bash
aea run
```
``` bash
cd ..
aea delete erc1155_deployer
aea delete erc1155_client
```
``` yaml
default_routing:
  fetchai/contract_api:0.8.0: fetchai/ledger:0.9.0
  fetchai/ledger_api:0.7.0: fetchai/ledger:0.9.0
  fetchai/oef_search:0.10.0: fetchai/soef:0.12.0
```
``` yaml
default_routing:
  fetchai/contract_api:0.8.0: fetchai/ledger:0.9.0
  fetchai/ledger_api:0.7.0: fetchai/ledger:0.9.0
  fetchai/oef_search:0.10.0: fetchai/soef:0.12.0
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```