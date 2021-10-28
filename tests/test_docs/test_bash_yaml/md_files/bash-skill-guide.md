``` bash
aea create my_aea && cd my_aea
aea scaffold skill my_search
```
``` bash
aea fingerprint skill fetchai/my_search:0.1.0
```
``` bash
aea add protocol fetchai/oef_search:1.0.0
```
``` bash
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/p2p_libp2p:0.25.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
```
``` bash
aea fetch fetchai/simple_service_registration:0.31.0 && cd simple_service_registration && aea install && aea build
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
aea_version: '>=1.0.0, <2.0.0'
fingerprint: {}
fingerprint_ignore_patterns: []
connections: []
contracts: []
protocols:
- fetchai/oef_search:1.0.0
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
    version: <2.0.0,>=1.0.0
is_abstract: false
```
``` yaml
name: simple_service_registration
author: fetchai
version: 0.20.0
type: skill
description: The simple service registration skills is a skill to register a service.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
fingerprint:
  README.md: QmUgCcR7sDBQeeCBRKwDT7tPBTi3t4zSibyEqR3xdQUKmh
  __init__.py: QmZd48HmYDr7FMxNaVeGfWRvVtieEdEV78hd7h7roTceP2
  behaviours.py: QmQHf6QL5aBtLJ34D2tdcbjJLbzom9gaA3HWgRn3rWyigM
  dialogues.py: QmTT9dvFhWt6qvxjwBfMFDTrgEtgWbvgANYafyRg2BXwcR
  handlers.py: QmZqPt8toGbJgTT6NZBLxjkusrQCZ8GmUEwcmqZ1sd7DpG
  strategy.py: QmVXfQpk4cjDw576H2ELE12tEiN5brPkwvffvcTeMbsugA
fingerprint_ignore_patterns: []
connections: []
contracts: []
protocols:
- fetchai/oef_search:1.0.0
skills: []
behaviours:
  service:
    args:
      max_soef_registration_retries: 5
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
      classification:
        piece: classification
        value: seller
      location:
        latitude: 51.5194
        longitude: 0.127
      personality_data:
        piece: genus
        value: data
      service_data:
        key: seller_service
        value: generic_service
    class_name: Strategy
dependencies: {}
is_abstract: false
```