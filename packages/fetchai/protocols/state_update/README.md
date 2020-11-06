# State Update Protocol

## Description

This is a protocol for updating the state of a decision maker.

## Specification

```yaml
---
name: state_update
author: fetchai
version: 0.7.0
description: A protocol for state updates to the decision maker state.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
speech_acts:
  initialize:
    exchange_params_by_currency_id: pt:dict[pt:str, pt:float]
    utility_params_by_good_id: pt:dict[pt:str, pt:float]
    amount_by_currency_id: pt:dict[pt:str, pt:int]
    quantities_by_good_id: pt:dict[pt:str, pt:int]
  apply:
    amount_by_currency_id: pt:dict[pt:str, pt:int]
    quantities_by_good_id: pt:dict[pt:str, pt:int]
...
---
initiation: [initialize]
reply:
  initialize: [apply]
  apply: [apply]
termination: [apply]
roles: {skill, decision_maker}
end_states: [successful]
...
```

## Links
