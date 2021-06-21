# Yoti Protocol

## Description

This is a protocol for communication between a Skill and the Yoti Connection.

## Specification

```yaml
---
name: yoti
author: fetchai
version: 1.0.0
description: A protocol for communication between yoti skills and yoti connection.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/yoti:1.0.0
speech_acts:
  get_profile:
    token: pt:str
    dotted_path: pt:str
    args: pt:list[pt:str]
  profile:
    info: pt:dict[pt:str, pt:str]
  error:
    error_code: pt:int
    error_msg: pt:str
...
---
initiation: [get_profile]
reply:
  get_profile: [profile, error]
  profile: []
  error: []
termination: [profile, error]
roles: {agent, yoti_server}
end_states: [successful, failed]
keep_terminal_state_dialogues: false
...
```

## Links
