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
name: two_party_negotiation
author: fetchai
version: 0.1.0
license: Apache-2.0
description: 'A protocol for negotiation over a fixed set of resources involving two parties.'
speech_acts:
  cfp:
    query: ct:DataModel
  propose:
    query: ct:DataModel
    price: pt:float
  accept: {}
  decline: {}
  match_accept: {}
```
