``` bash
sudo nano 99-hidraw-permissions.rules
```
``` bash
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0664", GROUP="plugdev"
```
``` bash
aea fetch fetchai/generic_seller:0.28.0
cd generic_seller
aea eject skill fetchai/generic_seller:0.27.0
cd ..
```
``` bash
aea fetch fetchai/generic_buyer:0.29.0
cd generic_buyer
aea eject skill fetchai/generic_buyer:0.26.0
cd ..
```
``` bash
aea init --reset --local --author fetchai
```
``` bash
aea create my_generic_seller
cd my_generic_seller
aea install
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
aea install
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
```
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
```
``` bash
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
```
``` bash
aea generate-wealth fetchai --sync
```
``` bash
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add protocol fetchai/fipa:1.0.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea run
```
``` bash 
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add protocol fetchai/fipa:1.0.0
aea add protocol fetchai/signing:1.0.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
```
``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}'
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
aea_version: '>=1.0.0, <2.0.0'
fingerprint:
  README.md: QmPb5kHYZyhUN87EKmuahyGqDGgqVdGPyfC1KpGC3xfmcP
  __init__.py: QmTSEedzQySy2nzRCY3F66CBSX52f8s3pWHZTejX4hKC9h
  behaviours.py: QmS9sPCv2yBnhWsmHeaCptpApMtYZipbR39TXixeGK64Ks
  dialogues.py: QmdTW8q1xQ7ajFVsWmuV62ypoT5J2b6Hkyz52LFaWuMEtd
  handlers.py: QmQnQhSaHPUYaJut8bMe2LHEqiZqokMSVfCthVaqrvPbdi
  strategy.py: QmYTUsfv64eRQDevCfMUDQPx2GCtiMLFdacN4sS1E4Fdfx
fingerprint_ignore_patterns: []
connections:
- fetchai/ledger:0.19.0
contracts: []
protocols:
- fetchai/default:1.0.0
- fetchai/fipa:1.0.0
- fetchai/ledger_api:1.0.0
- fetchai/oef_search:1.0.0
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
      data_for_sale:
        generic: data
      has_data_source: false
      is_ledger_tx: true
      location:
        latitude: 51.5194
        longitude: 0.127
      service_data:
        key: seller_service
        value: generic_service
      service_id: generic_service
      unit_price: 10
    class_name: GenericStrategy
is_abstract: false
dependencies: {}
```
``` yaml
name: generic_buyer
author: fetchai
version: 0.1.0
type: skill
description: The weather client skill implements the skill to purchase weather data.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
fingerprint:
  README.md: QmTR91jm7WfJpmabisy74NR5mc35YXjDU1zQAUKZeHRw8L
  __init__.py: QmU5vrC8FipyjfS5biNa6qDWdp4aeH5h4YTtbFDmCg8Chj
  behaviours.py: QmNwvSjEz4kzM3gWtnKbZVFJc2Z85Nb748CWAK4C4Sa4nT
  dialogues.py: QmNen91qQDWy4bNBKrB3LabAP5iRf29B8iwYss4NB13iNU
  handlers.py: QmZfudXXbdiREiViuwPZDXoQQyXT2ySQHdF7psQsohZXQy
  strategy.py: QmcrwaEWvKHDCNti8QjRhB4utJBJn5L8GpD27Uy9zHwKhY
fingerprint_ignore_patterns: []
connections:
- fetchai/ledger:0.19.0
contracts: []
protocols:
- fetchai/default:1.0.0
- fetchai/fipa:1.0.0
- fetchai/ledger_api:1.0.0
- fetchai/oef_search:1.0.0
- fetchai/signing:1.0.0
skills: []
behaviours:
  search:
    args:
      search_interval: 5
    class_name: GenericSearchBehaviour
  transaction:
    args:
      max_processing: 420
      transaction_interval: 2
    class_name: GenericTransactionBehaviour
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
      is_ledger_tx: true
      location:
        latitude: 51.5194
        longitude: 0.127
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      min_quantity: 1
      search_query:
        constraint_type: ==
        search_key: seller_service
        search_value: generic_service
      search_radius: 5.0
      service_id: generic_service
      stop_searching_on_result: true
    class_name: GenericStrategy
is_abstract: false
dependencies: {}
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```