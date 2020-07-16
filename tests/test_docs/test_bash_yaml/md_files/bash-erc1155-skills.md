``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea fetch fetchai/erc1155_deployer:0.9.0
cd erc1155_deployer
aea install
```
``` bash
aea create erc1155_deployer
cd erc1155_deployer
aea add connection fetchai/oef:0.6.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/erc1155_client:0.9.0
aea install
aea config set agent.default_connection fetchai/oef:0.6.0
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash
aea fetch fetchai/erc1155_client:0.9.0
cd erc1155_client
aea install
```
``` bash
aea create erc1155_client
cd erc1155_client
aea add connection fetchai/oef:0.6.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/erc1155_client:0.8.0
aea install
aea config set agent.default_connection fetchai/oef:0.6.0
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash
aea generate-wealth ethereum
```
``` bash
aea get-wealth ethereum
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
  fetchai/contract_api:0.1.0: fetchai/ledger:0.2.0
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.2.0
```
``` yaml
default_routing:
  fetchai/contract_api:0.1.0: fetchai/ledger:0.2.0
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.2.0
```
