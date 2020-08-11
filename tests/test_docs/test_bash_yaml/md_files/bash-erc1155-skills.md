``` bash
aea fetch fetchai/erc1155_deployer:0.11.0
cd erc1155_deployer
aea install
```
``` bash
aea create erc1155_deployer
cd erc1155_deployer
aea add connection fetchai/p2p_libp2p:0.6.0
aea add connection fetchai/soef:0.6.0
aea add connection fetchai/ledger:0.3.0
aea add skill fetchai/erc1155_deploy:0.11.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.6.0
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea fetch fetchai/erc1155_client:0.11.0
cd erc1155_client
aea install
```
``` bash
aea create erc1155_client
cd erc1155_client
aea add connection fetchai/p2p_libp2p:0.6.0
aea add connection fetchai/soef:0.6.0
aea add connection fetchai/ledger:0.3.0
aea add skill fetchai/erc1155_client:0.10.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.6.0
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
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
Successfully minted items. Transaction digest: ...
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
  fetchai/contract_api:0.2.0: fetchai/ledger:0.3.0
  fetchai/ledger_api:0.2.0: fetchai/ledger:0.3.0
  fetchai/oef_search:0.4.0: fetchai/soef:0.6.0
```
``` yaml
default_routing:
  fetchai/contract_api:0.2.0: fetchai/ledger:0.3.0
  fetchai/ledger_api:0.2.0: fetchai/ledger:0.3.0
  fetchai/oef_search:0.4.0: fetchai/soef:0.6.0
```
