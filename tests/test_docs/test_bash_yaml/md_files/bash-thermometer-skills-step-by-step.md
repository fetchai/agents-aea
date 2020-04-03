``` bash
sudo nano 99-hidraw-permissions.rules
```
``` bash
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0664", GROUP="plugdev"
```
``` bash
aea create my_thermometer
cd my_thermometer
```
``` bash
aea scaffold skill thermometer
```
``` bash
aea fingerprint skill thermometer
```
``` bash
aea create my_client
cd my_client
```
``` bash
aea scaffold skill thermometer_client
```
``` bash
aea fingerprint skill thermometer
```
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```
``` bash
aea generate-wealth fetchai
```
``` bash
aea add connection fetchai/oef:0.1.0
aea install
aea run --connections fetchai/oef:0.1.0
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash
aea add connection fetchai/oef:0.1.0
aea install
aea run --connections fetchai/oef:0.1.0
```
``` bash
cd ..
aea delete my_thermometer
aea delete my_client
```
``` yaml
name: thermometer
author: fetchai
version: 0.1.0
license: Apache-2.0
fingerprint: {}
aea_version: '>=0.3.0, <0.4.0'
description: "The thermometer skill implements the functionality to sell data."
behaviours:
  service_registration:
    class_name: ServiceRegistrationBehaviour
    args:
      services_interval: 60
handlers:
  fipa:
    class_name: FIPAHandler
    args: {}
models:
  strategy:
    class_name: Strategy
    args:
      price_per_row: 1
      seller_tx_fee: 0
      currency_id: 'FET'
      ledger_id: 'fetchai'
      has_sensor: True
      is_ledger_tx: True
  dialogues:
    class_name: Dialogues
    args: {}
protocols: ['fetchai/fipa:0.1.0', 'fetchai/oef_search:0.1.0', 'fetchai/default:0.1.0']
ledgers: ['fetchai']
dependencies:
  pyserial: {}
  temper-py: {}
```
``` yaml
name: thermometer_client
author: fetchai
version: 0.1.0
license: Apache-2.0
fingerprint: {}
aea_version: '>=0.3.0, <0.4.0'
description: "The thermometer client skill implements the skill to purchase temperature data."
behaviours:
  search:
    class_name: MySearchBehaviour
    args:
      search_interval: 5
handlers:
  fipa:
    class_name: FIPAHandler
    args: {}
  oef:
    class_name: OEFHandler
    args: {}
  transaction:
    class_name: MyTransactionHandler
    args: {}
models:
  strategy:
    class_name: Strategy
    args:
      country: UK
      max_row_price: 4
      max_tx_fee: 2000000
      currency_id: 'FET'
      ledger_id: 'fetchai'
      is_ledger_tx: True
  dialogues:
    class_name: Dialogues
    args: {}
protocols: ['fetchai/fipa:0.1.0','fetchai/default:0.1.0','fetchai/oef_search:0.1.0']
ledgers: ['fetchai']
```
``` yaml
addr: ${OEF_ADDR: 127.0.0.1}
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
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
```
``` yaml
max_buyer_tx_fee: 20000
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
```
