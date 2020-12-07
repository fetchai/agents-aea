``` bash
aea fetch fetchai/erc1155_deployer:0.19.0
cd erc1155_deployer
aea install
```
``` bash
aea create erc1155_deployer
cd erc1155_deployer
aea add connection fetchai/p2p_libp2p:0.12.0
aea add connection fetchai/soef:0.13.0
aea add connection fetchai/ledger:0.10.0
aea add skill fetchai/erc1155_deploy:0.18.0
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
aea fetch fetchai/erc1155_client:0.19.0
cd erc1155_client
aea install
```
``` bash
aea create erc1155_client
cd erc1155_client
aea add connection fetchai/p2p_libp2p:0.12.0
aea add connection fetchai/soef:0.13.0
aea add connection fetchai/ledger:0.10.0
aea add skill fetchai/erc1155_client:0.17.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.12.0
```
``` bash
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:0.8.0": "fetchai/ledger:0.10.0",
  "fetchai/ledger_api:0.7.0": "fetchai/ledger:0.10.0",
  "fetchai/oef_search:0.10.0": "fetchai/soef:0.13.0"
}'
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
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat erc1155_deployer/ethereum_private_key.txt),1000000000000000000000" --account="$(cat erc1155_client/ethereum_private_key.txt),1000000000000000000000"
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
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["'$(cd ../erc1155_deployer && aea get-multiaddress cosmos -c -i fetchai/p2p_libp2p:0.12.0 -u public_uri)'"],
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
aea delete erc1155_deployer
aea delete erc1155_client
```
``` yaml
default_routing:
  fetchai/contract_api:0.8.0: fetchai/ledger:0.10.0
  fetchai/ledger_api:0.7.0: fetchai/ledger:0.10.0
  fetchai/oef_search:0.10.0: fetchai/soef:0.13.0
```
``` yaml
default_routing:
  fetchai/contract_api:0.8.0: fetchai/ledger:0.10.0
  fetchai/ledger_api:0.7.0: fetchai/ledger:0.10.0
  fetchai/oef_search:0.10.0: fetchai/soef:0.13.0
```
``` yaml
---
public_id: fetchai/p2p_libp2p:0.12.0
type: connection
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers:
  - SOME_ADDRESS
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```