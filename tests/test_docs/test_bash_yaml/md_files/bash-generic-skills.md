``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea fetch fetchai/generic_seller:0.1.0 --alias my_seller_aea
cd generic_seller
aea install
```
``` bash
aea create my_seller_aea
cd my_seller_aea
aea add connection fetchai/oef:0.3.0
aea add skill fetchai/generic_seller:0.4.0
aea install
aea config set agent.default_connection fetchai/oef:0.3.0
```
``` bash
aea fetch fetchai/generic_buyer:0.1.0 --alias my_buyer_aea
cd generic_buyer
aea install
```
``` bash
aea create my_buyer_aea
cd my_buyer_aea
aea add connection fetchai/oef:0.3.0
aea add skill fetchai/generic_buyer:0.3.0
aea install
aea config set agent.default_connection fetchai/oef:0.3.0
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
aea run --connections fetchai/oef:0.3.0
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
ledger_apis:
  fetchai:
    network: testnet
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
    address: http://aea-testnet.sandbox.fetch-ai.com:1317
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
      seller_tx_fee: 0
      service_data:
        city: Cambridge
        country: UK
      total_price: 10
    class_name: Strategy 
```
``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      is_ledger_tx: true
      ledger_id: fetchai
      max_buyer_tx_fee: 1
      max_price: 4
      search_query:
        constraint_type: ==
        search_term: country
        search_value: UK
    class_name: Strategy
```
