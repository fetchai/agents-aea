# Register Protocol

## Description

This is a protocol for communication between two AEAs for registration.

## Specification

```yaml
---
name: register
author: fetchai
version: 0.3.0
description: A protocol for communication between two AEAs for registration.
license: Apache-2.0
aea_version: '>=0.8.0, <0.9.0'
speech_acts:
  register:
    info: pt:dict[pt:str, pt:str]
  success:
    info: pt:dict[pt:str, pt:str]
  error:
    error_code: pt:int
    error_msg: pt:str
    info: pt:dict[pt:str, pt:str]
...
---
initiation: [register]
reply:
  register: [success, error]
  success: []
  error: []
termination: [success, error]
roles: {agent}
end_states: [successful, failed]
keep_terminal_state_dialogues: true
...
```

## Links
