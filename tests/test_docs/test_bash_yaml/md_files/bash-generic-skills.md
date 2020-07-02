``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea fetch fetchai/generic_seller:0.2.0 --alias my_seller_aea
cd my_seller_aea
aea install
```
``` bash
aea create my_seller_aea
cd my_seller_aea
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea add skill fetchai/generic_seller:0.6.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
```
``` bash
aea fetch fetchai/generic_buyer:0.2.0 --alias my_buyer_aea
cd my_buyer_aea
aea install
```
``` bash
aea create my_buyer_aea
cd my_buyer_aea
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea add skill fetchai/generic_buyer:0.5.0
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
aea config set vendor.fetchai.skills.generic_seller.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.generic_seller.models.strategy.args.ledger_id ethereum
```
``` bash
aea config set vendor.fetchai.skills.generic_seller.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.generic_seller.models.strategy.args.ledger_id cosmos
```
``` bash
aea config set vendor.fetchai.skills.generic_buyer.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.generic_buyer.models.strategy.args.ledger_id ethereum
```
``` bash
aea config set vendor.fetchai.skills.generic_buyer.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.generic_buyer.models.strategy.args.ledger_id cosmos
```
``` bash
cd my_seller_aea
aea config set vendor.fetchai.skills.generic_seller.is_abstract false --type bool
```
``` bash
cd my_buyer_aea
aea config set vendor.fetchai.skills.generic_buyer.is_abstract false --type bool
```
``` bash
aea run
```
``` bash
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
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
``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      data_for_sale:
        pressure: 20
        temperature: 26
        wind: 10
      data_model:
        attribute_one:
          is_required: true
          name: country
          type: str
        attribute_two:
          is_required: true
          name: city
          type: str
      data_model_name: location
      has_data_source: false
      is_ledger_tx: true
      ledger_id: fetchai
      service_data:
        city: Cambridge
        country: UK
      service_id: generic_service
      unit_price: 10
    class_name: GenericStrategy 
```
``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      data_model:
        attribute_one:
          is_required: true
          name: country
          type: str
        attribute_two:
          is_required: true
          name: city
          type: str
      data_model_name: location
      is_ledger_tx: true
      ledger_id: fetchai
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      search_query:
        constraint_one:
          constraint_type: ==
          search_term: country
          search_value: UK
        constraint_two:
          constraint_type: ==
          search_term: city
          search_value: Cambridge
      service_id: generic_service
    class_name: GenericStrategy
```
