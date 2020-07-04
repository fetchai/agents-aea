``` bash
sudo nano 99-hidraw-permissions.rules
```
``` bash
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0664", GROUP="plugdev"
```
``` bash
aea fetch fetchai/generic_seller:0.3.0
cd generic_seller
aea eject skill fetchai/generic_seller:0.6.0
cd ..
```
``` bash
aea fetch fetchai/generic_buyer:0.3.0
cd generic_buyer
aea eject skill fetchai/generic_buyer:0.5.0
cd ..
```
``` bash
aea create my_generic_seller
cd my_generic_seller
```
``` bash
aea scaffold skill generic_seller
```
``` bash
aea fingerprint skill generic_seller
```
``` bash
aea create my_generic_buyer
cd my_generic_buyer
```
``` bash
aea scaffold skill generic_buyer
```
``` bash
aea fingerprint skill my_generic_buyer
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
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
aea run
```
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```
``` bash 
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
aea run
```
``` bash 
cd ..
aea delete my_generic_seller
aea delete my_generic_buyer
```
``` yaml
name: generic_seller
author: fetchai
version: 0.6.0
description: The weather station skill implements the functionality to sell weather
  data.
license: Apache-2.0
aea_version: '>=0.5.0, <0.6.0'
fingerprint:
  __init__.py: QmbfkeFnZVKppLEHpBrTXUXBwg2dpPABJWSLND8Lf1cmpG
  behaviours.py: QmTwUHrRrBvadNp4RBBEKcMBUvgv2MuGojz7gDsuYDrauE
  dialogues.py: QmY44eSrEzaZxtAG1dqbddwouj5iVMEitzpmt2xFC6MDUm
  handlers.py: QmSiquvAA4ULXPEJfmT3Z85Lqm9Td2H2uXXKuXrZjcZcPK
  strategy.py: QmYt74ucz8GfddfwP5dFgQBbD1dkcWvydUyEZ8jn9uxEDK
fingerprint_ignore_patterns: []
contracts: []
protocols:
- fetchai/default:0.3.0
- fetchai/fipa:0.4.0
- fetchai/ledger_api:0.1.0
- fetchai/oef_search:0.3.0
skills: []
behaviours:
  service_registration:
    args:
      services_interval: 20
    class_name: GenericServiceRegistrationBehaviour
handlers:
  fipa:
    args: {}
    class_name: GenericFipaHandler
  ledger_api:
    args: {}
    class_name: GenericLedgerApiHandler
  oef_search:
    args: {}
    class_name: GenericOefSearchHandler
models:
  default_dialogues:
    args: {}
    class_name: DefaultDialogues
  fipa_dialogues:
    args: {}
    class_name: FipaDialogues
  ledger_api_dialogues:
    args: {}
    class_name: LedgerApiDialogues
  oef_search_dialogues:
    args: {}
    class_name: OefSearchDialogues
  strategy:
    args:
      currency_id: FET
      data_for_sale:
        generic: data
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
dependencies: {}
```
``` yaml
name: generic_buyer
author: fetchai
version: 0.5.0
description: The generic buyer skill implements the skill to purchase data.
license: Apache-2.0
aea_version: '>=0.5.0, <0.6.0'
fingerprint:
  __init__.py: QmaEDrNJBeHCJpbdFckRUhLSBqCXQ6umdipTMpYhqSKxSG
  behaviours.py: QmYfAMPG5Rnm9fGp7frZLky6cV6Z7qAhtsPNhfwtVYRuEx
  dialogues.py: QmXe9VAuinv6jgi5So7e25qgWXN16pB6tVG1iD7oAxUZ56
  handlers.py: QmX9Pphv5VkfKgYriUkzqnVBELLkpdfZd6KzEQKkCG6Da3
  strategy.py: QmP3fLkBnLyQhHngZELHeLfK59WY6Xz76bxCVm6pfE6tLh
fingerprint_ignore_patterns: []
contracts: []
protocols:
- fetchai/default:0.3.0
- fetchai/fipa:0.4.0
- fetchai/ledger_api:0.1.0
- fetchai/oef_search:0.3.0
skills: []
behaviours:
  search:
    args:
      search_interval: 5
    class_name: GenericSearchBehaviour
handlers:
  fipa:
    args: {}
    class_name: GenericFipaHandler
  ledger_api:
    args: {}
    class_name: GenericLedgerApiHandler
  oef_search:
    args: {}
    class_name: GenericOefSearchHandler
  signing:
    args: {}
    class_name: GenericSigningHandler
models:
  default_dialogues:
    args: {}
    class_name: DefaultDialogues
  fipa_dialogues:
    args: {}
    class_name: FipaDialogues
  ledger_api_dialogues:
    args: {}
    class_name: LedgerApiDialogues
  oef_search_dialogues:
    args: {}
    class_name: OefSearchDialogues
  signing_dialogues:
    args: {}
    class_name: SigningDialogues
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
dependencies: {}
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
