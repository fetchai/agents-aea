# Fipa Protocol

## Description

This is a protocol for two agents to negotiate over a fixed set of resources.

## Specification

```yaml
---
name: fipa
author: fetchai
version: 0.10.0
description: A protocol for FIPA ACL.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
speech_acts:
  cfp:
    query: ct:Query
  propose:
    proposal: ct:Description
  accept_w_inform:
    info: pt:dict[pt:str, pt:str]
  match_accept_w_inform:
    info: pt:dict[pt:str, pt:str]
  inform:
    info: pt:dict[pt:str, pt:str]
  accept: {}
  decline: {}
  match_accept: {}
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
  cfp: [propose, decline]
  propose: [accept, accept_w_inform, decline, propose]
  accept: [decline, match_accept, match_accept_w_inform]
  accept_w_inform: [decline, match_accept, match_accept_w_inform]
  decline: []
  match_accept: [inform]
  match_accept_w_inform: [inform]
  inform: [inform]
termination: [decline, match_accept, match_accept_w_inform, inform]
roles: {seller, buyer}
end_states: [successful, declined_cfp, declined_propose, declined_accept]
...
```

## Links

* <a href="http://www.fipa.org" target="_blank">FIPA Foundation</a>