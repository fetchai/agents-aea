# Gym Protocol

## Description

This is a protocol for interacting with a gym connection.

## Specification

```yaml
---
name: gym
author: fetchai
version: 1.0.0
description: A protocol for interacting with a gym connection.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/gym:1.0.0
speech_acts:
  act:
    action: ct:AnyObject
    step_id: pt:int
  percept:
    step_id: pt:int
    observation: ct:AnyObject
    reward: pt:float
    done: pt:bool
    info: ct:AnyObject
  status:
    content: pt:dict[pt:str, pt:str]
  reset: {}
  close: {}
...
---
ct:AnyObject: |
  bytes any = 1;
...
---
initiation: [reset]
reply:
  reset: [status]
  status: [act, close, reset]
  act: [percept]
  percept: [act, close, reset]
  close: []
termination: [close]
roles: {agent, environment}
end_states: [successful]
keep_terminal_state_dialogues: false
...
```

## Links

* <a href="https://gym.openai.com" target="_blank">OpenAI Gym</a>
