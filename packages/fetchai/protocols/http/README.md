# HTTP Protocol

## Description

This is a protocol for interacting with a client/server via HTTP requests and responses.

## Specification

```yaml
---
name: http
author: fetchai
version: 1.0.0
description: A protocol for HTTP requests and responses.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/http:1.0.0
speech_acts:
  request:
    method: pt:str
    url: pt:str
    version: pt:str
    headers: pt:str
    body: pt:bytes
  response:
    version: pt:str
    status_code: pt:int
    status_text: pt:str
    headers: pt:str
    body: pt:bytes
...
---
initiation: [request]
reply:
  request: [response]
  response: []
termination: [response]
roles: {client, server}
end_states: [successful]
keep_terminal_state_dialogues: false
...
```

## Links

* <a href="https://www.w3.org/Protocols/rfc2616/rfc2616.html" target="_blank">HTTP Specification</a>
