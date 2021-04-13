# State Update Protocol

## Description

This is a protocol for updating the state of a decision maker.

## Specification

```yaml
---
name: state_update
author: fetchai
version: 1.0.0
description: A protocol for state updates to the decision maker state.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/state_update:1.0.0
speech_acts:
  initialize:
    exchange_params_by_currency_id: pt:dict[pt:str, pt:float]
    utility_params_by_good_id: pt:dict[pt:str, pt:float]
    amount_by_currency_id: pt:dict[pt:str, pt:int]
    quantities_by_good_id: pt:dict[pt:str, pt:int]
  apply:
    amount_by_currency_id: pt:dict[pt:str, pt:int]
    quantities_by_good_id: pt:dict[pt:str, pt:int]
  end: {}
...
---
initiation: [initialize]
reply:
  initialize: [apply]
  apply: [apply, end]
  end: []
termination: [end]
roles: {skill, decision_maker}
end_states: [successful]
keep_terminal_state_dialogues: false
...
```

## Links
