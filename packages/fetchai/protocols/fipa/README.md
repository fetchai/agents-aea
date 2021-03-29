# Fipa Protocol

## Description

This is a protocol for two agents to negotiate over a fixed set of resources.

## Specification

```yaml
---
name: fipa
author: fetchai
version: 1.0.0
description: A protocol for FIPA ACL.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/fipa:1.0.0
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
  end: {}
...
---
ct:Query: |
  bytes query_bytes = 1;
ct:Description: |
  bytes description_bytes = 1;
...
---
initiation: [cfp]
reply:
  cfp: [propose, decline]
  propose: [accept, accept_w_inform, decline, propose]
  accept: [decline, match_accept, match_accept_w_inform]
  accept_w_inform: [decline, match_accept, match_accept_w_inform]
  decline: []
  match_accept: [inform, end]
  match_accept_w_inform: [inform, end]
  inform: [inform, end]
  end: []
termination: [decline, end]
roles: {seller, buyer}
end_states: [successful, declined_cfp, declined_propose, declined_accept]
keep_terminal_state_dialogues: true
...
```

## Links

* <a href="http://www.fipa.org" target="_blank">FIPA Foundation</a>
