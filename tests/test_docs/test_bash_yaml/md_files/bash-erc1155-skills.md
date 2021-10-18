``` bash
aea fetch fetchai/erc1155_deployer:0.33.0
cd erc1155_deployer
aea install
aea build
```
``` bash
aea create erc1155_deployer
cd erc1155_deployer
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/erc1155_deploy:0.30.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-ethereum": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-cosmos": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
aea install
aea build
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
```
``` bash
aea fetch fetchai/erc1155_client:0.33.0
cd erc1155_client
aea install
aea build
```
``` bash
aea create erc1155_client
cd erc1155_client
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/erc1155_client:0.28.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-ethereum": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-cosmos": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
aea install
aea build
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
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
aea delete erc1155_deployer
aea delete erc1155_client
```
``` yaml
default_routing:
  fetchai/contract_api:1.0.0: fetchai/ledger:0.19.0
  fetchai/ledger_api:1.0.0: fetchai/ledger:0.19.0
  fetchai/oef_search:1.0.0: fetchai/soef:0.26.0
```
``` yaml
default_routing:
  fetchai/contract_api:1.0.0: fetchai/ledger:0.19.0
  fetchai/ledger_api:1.0.0: fetchai/ledger:0.19.0
  fetchai/oef_search:1.0.0: fetchai/soef:0.26.0
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