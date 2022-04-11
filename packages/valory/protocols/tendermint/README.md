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
  tendermint_config_request:
    query: pt:str
  tendermint_config_response:
    info: pt:dict[pt:str, pt:str]
  error:
    error_code: ct:ErrorCode
    error_msg: pt:str
    info: pt:dict[pt:str, pt:str]
...
---
ct:ErrorCode: |
  enum ErrorCodeEnum {
      INVALID_REQUEST = 0;
    }
  ErrorCodeEnum error_code = 1;
...
---
initiation: [tendermint_config_request]
reply:
  tendermint_config_request: [tendermint_config_response, error]
  tendermint_config_response: []
  error: []
roles: {agent}
termination: [tendermint_config_response, error]
end_states: [config_shared, config_not_shared]
keep_terminal_state_dialogues: true
...
```

## Links

