# Consensus Protocol

## Description

This is a consensus protocol for aggregating observations.

## Specification

```yaml
---
name: consensus
author: fetchai
version: 0.1.0
description: A protocol for agents to aggregate individual observations
license: Apache-2.0
aea_version: '>=0.9.0, <0.10.0'
speech_acts:
  observation:
    value: pt:int
    time: pt:int
    source: pt:str
    signature: pt:str
  aggregation:
    value: pt:int
    time: pt:int
    contributors: pt:list[pt:int]
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
protocol_specification_id: 0.1.0
...
```

## Links
