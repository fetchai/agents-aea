# Prometheus Protocol

## Description

This is a protocol for interacting with prometheus connection.

## Specification

```yaml
---
name: prometheus
author: fetchai
version: 1.0.0
description: A protocol for adding and updating metrics to a prometheus server.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/prometheus:1.0.0
speech_acts:
  add_metric:
    type: pt:str
    title: pt:str
    description: pt:str
    labels: pt:dict[pt:str, pt:str]
  update_metric:
    title: pt:str
    callable: pt:str
    value: pt:float
    labels: pt:dict[pt:str, pt:str]
  response:
    code: pt:int
    message: pt:optional[pt:str]
...
---
initiation: [add_metric, update_metric]
reply:
  add_metric: [response]
  update_metric: [response]
  response: []
termination: [response]
roles: {agent, server}
end_states: [successful]
keep_terminal_state_dialogues: false
...
```

## Links
