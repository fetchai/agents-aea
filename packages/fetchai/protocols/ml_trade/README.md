# ML Trade Protocol

## Description

This is a protocol for trading data for training and prediction purposes.

## Specification

```yaml
---
name: ml_trade
author: fetchai
version: 0.9.0
description: A protocol for trading data for training and prediction purposes.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
speech_acts:
  cfp:
    query: ct:Query
  terms:
    terms: ct:Description
  accept:
    terms: ct:Description
    tx_digest: pt:str
  data:
    terms: ct:Description
    payload: pt:bytes
...
---
ct:Query: |
  message Nothing {
  }
  oneof query{
      bytes bytes = 1;
      Nothing nothing = 2;
      bytes query_bytes = 3;
  }
ct:Description: |
  bytes description = 1;
...
---
initiation: [cfp]
reply:
  cfp: [terms]
  terms: [accept]
  accept: [data]
  data: []
termination: [data]
roles: {seller, buyer}
end_states: [successful]
...
```

## Links
