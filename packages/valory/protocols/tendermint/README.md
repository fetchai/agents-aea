# Tendermint Protocol

## Description

This is a protocol for communication between AEAs for sharing their tendermint configuration details.

## Specification

```yaml
---
name: tendermint
author: valory
version: 0.1.0
protocol_specification_id: valory/tendermint:0.1.0
description: A protocol for communication between two AEAs to share tendermint configuration details.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
speech_acts:
  request: 
    query: pt:optional[pt:str]  # required field, optional provides default value, not used otherwise.
  response:
    info: pt:str
  error:
    error_code: ct:ErrorCode
    error_msg: pt:str
    error_data: pt:dict[pt:str, pt:str]
...
---
ct:ErrorCode: |
  enum ErrorCodeEnum {
      INVALID_REQUEST = 0;
    }
  ErrorCodeEnum error_code = 1;
...
---
initiation: [request]
reply:
  request: [response, error]
  response: []
  error: []
roles: {agent}
termination: [response, error]
end_states: [config_shared, config_not_shared]
keep_terminal_state_dialogues: true
...
```

## Links

