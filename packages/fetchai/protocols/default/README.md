# Default Protocol

## Description

This is a protocol for two agents exchanging any bytes messages.

## Specification

```yaml
---
name: default
author: fetchai
version: 0.9.0
description: A protocol for exchanging any bytes message.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
speech_acts:
  bytes:
    content: pt:bytes
  error:
    error_code: ct:ErrorCode
    error_msg: pt:str
    error_data: pt:dict[pt:str, pt:bytes]
...
---
ct:ErrorCode: |
  enum ErrorCodeEnum {
      UNSUPPORTED_PROTOCOL = 0;
      DECODING_ERROR = 1;
      INVALID_MESSAGE = 2;
      UNSUPPORTED_SKILL = 3;
      INVALID_DIALOGUE = 4;
    }
  ErrorCodeEnum error_code = 1;
...
---
initiation: [bytes, error]
reply:
  bytes: [bytes, error]
  error: []
termination: [bytes, error]
roles: {agent}
end_states: [successful, failed]
...
```

## Links
