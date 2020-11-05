``` bash
sudo nano 99-hidraw-permissions.rules
```
``` bash
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0664", GROUP="plugdev"
```
``` bash
aea fetch fetchai/generic_seller:0.13.0
cd generic_seller
aea eject skill fetchai/generic_seller:0.16.0
cd ..
```
``` bash
aea fetch fetchai/generic_buyer:0.13.0
cd generic_buyer
aea eject skill fetchai/generic_buyer:0.15.0
cd ..
```
``` bash
aea init --reset --local --author fetchai
```
``` bash
aea create my_generic_seller
cd my_generic_seller
```
``` bash
aea scaffold skill generic_seller
```
``` bash
aea fingerprint skill fetchai/generic_seller:0.1.0
```
``` bash
aea create my_generic_buyer
cd my_generic_buyer
```
``` bash
aea scaffold skill generic_buyer
```
``` bash
aea fingerprint skill fetchai/generic_buyer:0.1.0
```
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
```
``` bash
aea generate-wealth fetchai --sync
```
``` bash
aea add connection fetchai/p2p_libp2p:0.12.0
aea add connection fetchai/soef:0.12.0
aea add connection fetchai/ledger:0.9.0
aea add protocol fetchai/fipa:0.10.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.12.0
aea run
```
``` bash 
aea add connection fetchai/p2p_libp2p:0.12.0
aea add connection fetchai/soef:0.12.0
aea add connection fetchai/ledger:0.9.0
aea add protocol fetchai/fipa:0.10.0
aea add protocol fetchai/signing:0.7.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.12.0
```
``` bash
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
version: 0.1.0
type: skill
description: The weather station skill implements the functionality to sell weather
  data.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
fingerprint:
  __init__.py: QmNkZAetyctaZCUf6ACxP5onGWsSxu2hjSNoFmJ3ta6Lta
  behaviours.py: QmcFahpL4DZ1rsTNEK1BT3e5T8TEJJg2hP4ytkzdqKuJnZ
  dialogues.py: QmRmoFp9xi1p1THVBYym9xEwW88KgkBHgz45LgrYbBecQw
  handlers.py: QmT4nvKikWXfGAEdRS8Qn8w89Gbh5zPb4EDB6EwPVP2YDJ
  strategy.py: QmP69kCtcovLD2Z7quESuNxVEyNuiZgqqbwozp6wAbvBCd
fingerprint_ignore_patterns: []
contracts: []
protocols:
- fetchai/default:0.9.0
- fetchai/fipa:0.10.0
- fetchai/ledger_api:0.7.0
- fetchai/oef_search:0.10.0
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
      has_data_source: false
      is_ledger_tx: true
      ledger_id: fetchai
      location:
        latitude: 51.5194
        longitude: 0.127
      service_data:
        key: seller_service
        value: generic_service
      service_id: generic_service
      unit_price: 10
    class_name: GenericStrategy
dependencies: {}
```
``` yaml
name: generic_buyer
author: fetchai
version: 0.1.0
type: skill
description: The weather client skill implements the skill to purchase weather data.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
fingerprint:
  __init__.py: QmNkZAetyctaZCUf6ACxP5onGWsSxu2hjSNoFmJ3ta6Lta
  behaviours.py: QmUBQvZkoCcik71vqRZGP4JJBgFP2kj8o7C24dfkAphitP
  dialogues.py: Qmf3McwyT5wMv3BzoN1L3ssqZzEq19LShEjQueiKqvADcX
  handlers.py: QmQVmi3GnuYJ5VM4trYjUeJyFHVfrUeMGDsRmtNCuntKA8
  strategy.py: QmQHQsjAsPiox5zMtMHhdhhhHt4rKq3cs3bqnwjgGSFp6n
fingerprint_ignore_patterns: []
contracts: []
protocols:
- fetchai/default:0.9.0
- fetchai/fipa:0.10.0
- fetchai/ledger_api:0.7.0
- fetchai/oef_search:0.10.0
- fetchai/signing:0.7.0
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
      is_ledger_tx: true
      ledger_id: fetchai
      location:
        latitude: 51.5194
        longitude: 0.127
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      search_query:
        constraint_type: ==
        search_key: seller_service
        search_value: generic_service
      search_radius: 5.0
      service_id: generic_service
    class_name: GenericStrategy
dependencies: {}
```
``` yaml
addr: ${OEF_ADDR: 127.0.0.1}
```
``` yaml
default_routing:
  fetchai/ledger_api:0.7.0: fetchai/ledger:0.9.0
  fetchai/oef_search:0.10.0: fetchai/soef:0.12.0
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```