``` bash
aea create my_aea && cd my_aea
aea scaffold skill my_search
```
``` bash
aea fingerprint skill fetchai/my_search:0.1.0
```
``` bash
aea add protocol fetchai/oef_search:0.14.0
```
``` bash
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/p2p_libp2p:0.17.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
}'
```
``` bash
aea fetch fetchai/simple_service_registration:0.23.0 && cd simple_service_registration && aea install && aea build
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
aea run
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
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAm1uJpFsqSgHStJdtTBPpDme1fo8uFEvvY182D2y89jQuj"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}'
```
``` bash
aea run
```
``` yaml
name: my_search
author: fetchai
version: 0.1.0
type: skill
description: A simple search skill utilising the SOEF search node.
license: Apache-2.0
aea_version: '>=0.11.0, <0.12.0'
fingerprint: {}
fingerprint_ignore_patterns: []
connections: []
contracts: []
protocols:
- fetchai/oef_search:0.14.0
skills: []
behaviours:
  my_search_behaviour:
    args:
      location:
        latitude: 51.5194
        longitude: 0.127
      search_query:
        constraint_type: ==
        search_key: seller_service
        search_value: generic_service
      search_radius: 5.0
      tick_interval: 5
    class_name: MySearchBehaviour
handlers:
  my_search_handler:
    args: {}
    class_name: MySearchHandler
models:
  oef_search_dialogues:
    args: {}
    class_name: OefSearchDialogues
dependencies:
  aea-ledger-fetchai:
    version: <0.2.0,>=0.1.0
is_abstract: false
```
``` yaml
name: simple_service_registration
author: fetchai
version: 0.4.0
type: skill
description: The simple service registration skills is a skill to register a service.
license: Apache-2.0
aea_version: '>=0.11.0, <0.12.0'
fingerprint:
  __init__.py: QmNkZAetyctaZCUf6ACxP5onGWsSxu2hjSNoFmJ3ta6Lta
  behaviours.py: QmRr1oe3zWKyPcktzKP4BiKqjCqmKjEDdLUQhn1JzNm4nD
  dialogues.py: QmayFh6ytPefJng5ENTUg46zsd6guHCZSsG3Cc2sy3xz6y
  handlers.py: QmViyyV5KvR3kkLEMpvDfqH5QtHowTbnpDxRYnKABpVvpC
  strategy.py: Qmdp6LCPZSnnyfM4EdRDTGZPqwxiJ3A1jsc3oF2Hv4m5Mv
fingerprint_ignore_patterns: []
connections: []
contracts: []
protocols:
- fetchai/oef_search:0.14.0
skills: []
behaviours:
  service:
    args:
      services_interval: 30
    class_name: ServiceRegistrationBehaviour
handlers:
  oef_search:
    args: {}
    class_name: OefSearchHandler
models:
  oef_search_dialogues:
    args: {}
    class_name: OefSearchDialogues
  strategy:
    args:
      location:
        latitude: 51.5194
        longitude: 0.127
      service_data:
        key: seller_service
        value: generic_service
    class_name: Strategy
dependencies:
  aea-ledger-fetchai:
    version: <0.2.0,>=0.1.0
is_abstract: false
```