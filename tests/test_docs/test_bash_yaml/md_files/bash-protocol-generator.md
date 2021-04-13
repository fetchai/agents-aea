``` bash
aea generate protocol <path-to-protocol-specification>
```
``` bash
aea generate protocol --l <language> <path-to-protocol-specification>
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
description: An example of a protocol specification that describes a protocol for bilateral negotiation.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
speech_acts:
  cfp:
    query: ct:Query
  propose:
    price: pt:float
    proposal: pt:dict[pt:str, pt:str]
    conditions: pt:optional[pt:union[pt:str, pt:dict[pt:str,pt:str], pt:set[pt:str]]]
    resources: pt:list[pt:bytes]
  accept: {}
  decline: {}
...
---
ct:Query: |
  bytes query_bytes = 1;
...
---
initiation: [cfp]
reply:
  cfp: [propose, decline]
  propose: [propose, accept, decline]
  accept: []
  decline: []
termination: [accept, decline]
roles: {buyer, seller}
end_states: [agreement_reached, agreement_unreached]
keep_terminal_state_dialogues: true
...
```
