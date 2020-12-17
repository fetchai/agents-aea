``` bash
aea generate protocol <path-to-protocol-specification>
```
``` bash
aea create my_aea
cd my_aea
```
``` bash
aea generate protocol ../examples/protocol_specification_ex/sample.yaml
```
``` yaml
---
name: two_party_negotiation
author: fetchai
version: 0.1.0
license: Apache-2.0
aea_version: '>=0.8.0, <0.9.0'
description: 'A protocol for negotiation over a fixed set of resources involving two parties.'
speech_acts:
  cfp:
    query: ct:DataModel
  propose:
    offer: ct:DataModel
    price: pt:float
  accept: {}
  decline: {}
  match_accept: {}
...
---
ct:DataModel: |
  bytes data_model = 1;
...
---
reply:
  cfp: [propose, decline]
  propose: [accept, decline]
  accept: [decline, match_accept]
  decline: []
  match_accept: []
roles: {buyer, seller}
end_states: [successful, failed]
...
```
