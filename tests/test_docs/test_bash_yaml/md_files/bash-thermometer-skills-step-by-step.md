``` bash
sudo nano 99-hidraw-permissions.rules
```
``` bash
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0664", GROUP="plugdev"
```
``` bash
aea create my_aea
cd my_aea
```
``` bash
aea scaffold skill thermometer
```
``` bash
aea create my_client
cd my_client
```
``` bash
aea scaffold skill thermometer_client
```
``` bash
addr: ${OEF_ADDR: 127.0.0.1}
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
aea delete my_weather_station
aea delete my_weather_client
```
``` yaml
name: thermometer
author: fetchai
version: 0.1.0
license: Apache-2.0
fingerprint: ""
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
     price: 1
     seller_tx_fee: 0
     currency_id: 'FET'
     ledger_id: 'fetchai'
     has_sensor: True
     is_ledger_tx: True
 dialogues:
   class_name: Dialogues
   args: {}
protocols: ['fetchai/fipa:0.1.0', 'fetchai/oef:0.1.0', 'fetchai/default:0.1.0']
ledgers: ['fetchai']
dependencies:
 pyserial: {}
 temper-py: {}
```
``` yaml
aea_version: 0.2.0
agent_name: my_aea
author: author
connections:
- fetchai/oef:0.1.0
- fetchai/stub:0.1.0
default_connection: fetchai/stub:0.1.0
default_ledger: fetchai
description: ''
fingerprint: ''
ledger_apis: {}
license: Apache-2.0
logging_config:
 disable_existing_loggers: false
 version: 1
private_key_paths: {}
protocols:
- fetchai/default:0.1.0
registry_path: ../packages
skills:
- author/thermometer:0.1.0
- fetchai/error:0.1.0
version: 0.1.0
```
``` yaml

name: thermometer_client
author: fetchai
version: 0.1.0
license: Apache-2.0
fingerprint: ""
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
protocols: ['fetchai/fipa:0.1.0','fetchai/default:0.1.0','fetchai/oef:0.1.0']
ledgers: ['fetchai']
```
``` yaml

aea_version: 0.2.0
agent_name: m_client
author: author
connections:
- fetchai/stub:0.1.0
default_connection: fetchai/stub:0.1.0
default_ledger: fetchai
description: ''
fingerprint: ''
ledger_apis: {}
license: Apache-2.0
logging_config:
 disable_existing_loggers: false
 version: 1
private_key_paths: {}
protocols:
- fetchai/default:0.1.0
registry_path: ../packages
skills:
- author/thermometer_client:0.1.0
- fetchai/error:0.1.0
version: 0.1.0
```
``` yaml
skills:
- my_authos/thermometer:0.1.0
- fetchai/error:0.1.0
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
