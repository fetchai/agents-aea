``` bash
aea fetch fetchai/coin_price_oracle:0.9.0
cd coin_price_oracle
aea install
aea build
```
``` bash
aea create coin_price_oracle
cd coin_price_oracle
aea add connection fetchai/http_client:0.19.0
aea add connection fetchai/ledger:0.15.0
aea add connection fetchai/p2p_libp2p:0.18.0
aea add skill fetchai/advanced_data_request:0.1.0
aea add skill fetchai/simple_oracle:0.8.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.3.0,>=0.2.0"},
  "aea-ledger-ethereum": {"version": "<0.3.0,>=0.2.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.18.0
aea install
aea build
```
```bash
aea config set --type str vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.url "https://api.coingecko.com/api/v3/simple/price?ids=fetch-ai&vs_currencies=usd"
```
```bash
aea config set --type list vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.outputs '[{"name": "price", "json_path": "fetch-ai.usd"}]'
```
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:0.12.0": "fetchai/ledger:0.15.0",
"fetchai/http:0.13.0": "fetchai/http_client:0.19.0",
"fetchai/ledger_api:0.11.0": "fetchai/ledger:0.15.0"
}'
```
```bash
LEDGER_ID=fetchai
```
```bash
LEDGER_ID=ethereum
```
```bash
aea config set agent.default_ledger $LEDGER_ID
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": '"\"$LEDGER_ID\""', "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
```
``` bash
aea generate-key $LEDGER_ID
aea add-key $LEDGER_ID
```
```bash
aea generate-wealth $LEDGER_ID
```
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
```
``` bash
aea fetch fetchai/coin_price_oracle_client:0.6.0
cd coin_price_oracle_client
aea install
aea build
```
``` bash
aea create coin_price_oracle_client
cd coin_price_oracle_client
aea add connection fetchai/http_client:0.19.0
aea add connection fetchai/ledger:0.15.0
aea add skill fetchai/simple_oracle_client:0.6.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.3.0,>=0.2.0"},
  "aea-ledger-ethereum": {"version": "<0.3.0,>=0.2.0"}
}'
aea config set agent.default_connection fetchai/ledger:0.15.0
aea install
aea build
```
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:0.12.0": "fetchai/ledger:0.15.0",
"fetchai/http:0.13.0": "fetchai/http_client:0.19.0",
"fetchai/ledger_api:0.11.0": "fetchai/ledger:0.15.0"
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
info: [coin_price_oracle] Oracle contract successfully deployed at address: ...
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
