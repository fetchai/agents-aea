# Aggregation Protocol

## Description

This is an aggregation protocol for aggregating observations.

## Specification

```yaml
---
name: aggregation
author: fetchai
version: 0.1.0
description: A protocol for agents to aggregate individual observations
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/aggregation:0.1.0
speech_acts:
  observation:
    value: pt:int
    time: pt:str
    source: pt:str
    signature: pt:str
  aggregation:
    value: pt:int
    time: pt:str
    contributors: pt:list[pt:str]
    signature: pt:str
...
---
initiation: [observation, aggregation]
reply:
  observation: []
  aggregation: []
termination: [observation, aggregation]
roles: {agent}
end_states: [successful, failed]
keep_terminal_state_dialogues: false
...
```

## Links
