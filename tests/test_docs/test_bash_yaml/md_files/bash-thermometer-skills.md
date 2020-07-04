``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash 
aea fetch fetchai/thermometer_aea:0.4.0 --alias my_thermometer_aea
cd thermometer_aea
aea install
```
``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea add skill fetchai/thermometer:0.5.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
```
``` bash
aea fetch fetchai/thermometer_client:0.4.0 --alias my_thermometer_client
cd my_thermometer_client
aea install
```
``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea add skill fetchai/thermometer_client:0.4.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
```
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```
``` bash
aea generate-wealth fetchai
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash
aea generate-wealth ethereum
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
```
``` bash
aea generate-wealth cosmos
```
``` bash
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.ledger_id ethereum
```
``` bash
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.ledger_id cosmos
```
``` bash
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.ledger_id ethereum
```
``` bash
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.ledger_id cosmos
```
``` bash
aea run
```
``` bash
cd ..
aea delete my_thermometer_aea
aea delete my_thermometer_client
```
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.1.0
```
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.1.0
```
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```
``` yaml
ledger_apis:
  cosmos:
    address: https://rest-agent-land.prod.fetch-ai.com:443
```
