``` bash
aea fetch fetchai/coin_price_oracle:0.17.4
cd coin_price_oracle
aea install
```
``` bash
aea create coin_price_oracle
cd coin_price_oracle
aea add connection fetchai/http_client:0.24.4
aea add connection fetchai/ledger:0.21.3
aea add connection fetchai/prometheus:0.9.4
aea add skill fetchai/advanced_data_request:0.7.4
aea add skill fetchai/simple_oracle:0.16.3
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-ethereum": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/ledger:0.21.3
aea install
```
``` bash
aea config set --type str vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.url "https://api.coingecko.com/api/v3/simple/price?ids=fetch-ai&vs_currencies=usd"
```
``` bash
aea config set --type list vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.outputs '[{"name": "price", "json_path": "fetch-ai.usd"}]'
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.oracle_value_name price
```
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:1.1.4": "fetchai/ledger:0.21.3",
"fetchai/http:1.1.4": "fetchai/http_client:0.24.4",
"fetchai/ledger_api:1.1.4": "fetchai/ledger:0.21.3"
}'
```
``` bash
aea config set agent.default_ledger fetchai
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.ledger_id fetchai
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.update_function update_oracle_value
```
``` bash
LEDGER_ID=fetchai
```
``` bash
LEDGER_ID=ethereum
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.ledger_id ethereum
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.update_function updateOracleValue
```
``` bash
aea generate-key $LEDGER_ID --add-key
```
``` bash
aea generate-wealth $LEDGER_ID
```
``` bash
aea fetch fetchai/coin_price_oracle_client:0.12.4
cd coin_price_oracle_client
aea install
```
``` bash
aea create coin_price_oracle_client
cd coin_price_oracle_client
aea add connection fetchai/http_client:0.24.4
aea add connection fetchai/ledger:0.21.3
aea add skill fetchai/simple_oracle_client:0.13.3
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"},
  "aea-ledger-ethereum": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/ledger:0.21.3
aea install
```
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:1.1.4": "fetchai/ledger:0.21.3",
"fetchai/http:1.1.4": "fetchai/http_client:0.24.4",
"fetchai/ledger_api:1.1.4": "fetchai/ledger:0.21.3"
}'
```
``` bash
aea config set agent.default_ledger fetchai
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.ledger_id fetchai
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.query_function query_oracle_value
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.ledger_id ethereum
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.query_function queryOracleValue
```
``` bash
aea generate-key $LEDGER_ID --add-key
```
``` bash
aea generate-wealth $LEDGER_ID
```
``` bash
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat coin_price_oracle/ethereum_private_key.txt),1000000000000000000000" --account="$(cat coin_price_oracle_client/ethereum_private_key.txt),1000000000000000000000"
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.erc20_address $ERC20_ADDRESS
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.erc20_address $ERC20_ADDRESS
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
aea config set vendor.fetchai.skills.simple_oracle_client.models.strategy.args.oracle_contract_address $ORACLE_ADDRESS
```
``` bash
Oracle contract successfully deployed at address: ORACLE_ADDRESS
```
``` bash
aea run
```
``` bash
info: [coin_price_oracle_client] Oracle client contract successfully deployed at address: ...
...
info: [coin_price_oracle_client] Oracle value successfully requested!
```
