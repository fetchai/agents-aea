``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea fetch fetchai/thermometer_aea:0.3.0 --alias my_thermometer_aea
cd my_thermometer_aea
aea install
```
``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger_api:0.1.0
aea add skill fetchai/thermometer:0.5.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
```
``` bash
aea fetch fetchai/thermometer_client:0.3.0 --alias my_thermometer_client
cd my_thermometer_client
aea install
```
``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger_api:0.1.0
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
aea install
```
``` bash
aea eject skill fetchai/thermometer:0.6.0
```
``` bash
aea fingerprint skill {YOUR_AUTHOR_HANDLE}/thermometer:0.1.0
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
  fetchai/ledger_api:0.1.0: fetchai/ledger_api:0.1.0
```
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger_api:0.1.0
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
        temperature: 26
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
    class_name: Strategy
dependencies:
  SQLAlchemy: {}
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
    class_name: Strategy
```
``` yaml
models:
  ...
  strategy:
    args:
      currency_id: ETH
      data_for_sale:
        temperature: 26
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
      ledger_id: ethereum
      service_data:
        city: Cambridge
        country: UK
      service_id: generic_service
      unit_price: 10
    class_name: Strategy
dependencies:
  SQLAlchemy: {}
```
``` yaml
models:
  ...
  strategy:
    args:
      currency_id: ETH
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
      ledger_id: ethereum
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
    class_name: Strategy
```
