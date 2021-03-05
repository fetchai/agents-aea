``` bash
aea fetch fetchai/coin_price_oracle:0.7.0
cd coin_price_oracle
aea install
aea build
```
``` bash
aea create coin_price_oracle
cd coin_price_oracle
aea add connection fetchai/http_client:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add connection fetchai/p2p_libp2p:0.17.0
aea add skill fetchai/coin_price:0.6.0
aea add skill fetchai/simple_oracle:0.6.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"},
  "aea-ledger-ethereum": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea install
```
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:0.12.0": "fetchai/ledger:0.14.0",
"fetchai/http:0.13.0": "fetchai/http_client:0.18.0",
"fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0"
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum
```
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
```
``` bash
aea fetch fetchai/coin_price_oracle_client:0.4.0
cd coin_price_oracle_client
aea install
```
``` bash
aea create coin_price_oracle_client
cd coin_price_oracle_client
aea add connection fetchai/http_client:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/simple_oracle_client:0.5.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"},
  "aea-ledger-ethereum": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/ledger:0.14.0
aea install
```
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:0.12.0": "fetchai/ledger:0.14.0",
"fetchai/http:0.13.0": "fetchai/http_client:0.18.0",
"fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0"
}'
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum
```
``` bash
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat coin_price_oracle/ethereum_private_key.txt),1000000000000000000000" --account="$(cat coin_price_oracle_client/ethereum_private_key.txt),1000000000000000000000"
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.erc20_address ERC20_ADDRESS
```
``` bash
aea run
```
``` bash
info: [coin_price_oracle] Oracle contract successfully deployed!
...
info: [coin_price_oracle] Oracle role successfully granted!
...
info: [coin_price_oracle] Oracle value successfully updated!
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.erc20_address ERC20_ADDRESS
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.oracle_contract_address ORACLE_ADDRESS
```
``` bash
aea run
```
``` bash
info: [coin_price_oracle_client] Oracle client contract successfully deployed!
...
info: [coin_price_oracle_client] Oracle client transactions approved!
...
info: [coin_price_oracle_client] Oracle value successfully requested!
```
