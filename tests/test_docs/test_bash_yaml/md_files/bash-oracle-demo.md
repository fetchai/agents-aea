``` bash
aea fetch fetchai/coin_price_oracle:0.3.0
cd coin_price_oracle
aea install
aea build
```
``` bash
aea create coin_price_oracle
cd coin_price_oracle
aea add connection fetchai/http_client:0.16.0
aea add connection fetchai/ledger:0.12.0
aea add connection fetchai/p2p_libp2p:0.14.0
aea add skill fetchai/coin_price:0.3.0
aea add skill fetchai/simple_oracle:0.3.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.14.0
```
``` bash
aea config set --type dict agent.default_routing \
'{
"fetchai/contract_api:0.10.0": "fetchai/ledger:0.12.0",
"fetchai/http:0.11.0": "fetchai/http_client:0.16.0",
"fetchai/ledger_api:0.9.0": "fetchai/ledger:0.12.0"
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
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
```
``` bash
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat coin_price_oracle/ethereum_private_key.txt),1000000000000000000000"
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