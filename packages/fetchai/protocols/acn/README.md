# ACN Protocol

## Description

This is a protocol for ACN (agent communication network) envelope delivery.

## Specification

```yaml
---
name: acn
author: fetchai
version: 1.0.0
description: The protocol used for envelope delivery on the ACN.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: aea/acn:1.0.0
speech_acts:
  register:
    record: ct:AgentRecord
  lookup_request:
    agent_address: pt:str
  lookup_response:
    record: ct:AgentRecord
  aea_envelope:
    envelope: pt:bytes
    record: ct:AgentRecord
  status:
    body: ct:StatusBody
...
---
ct:AgentRecord:
  string service_id = 1;
  string ledger_id = 2;
  string address = 3;
  string public_key = 4;
  string peer_public_key = 5;
  string signature = 6;
  string not_before = 7;
  string not_after = 8;
ct:StatusBody: |
  enum StatusCodeEnum {
    // common (0x)
    SUCCESS = 0;
    ERROR_UNSUPPORTED_VERSION = 1;
    ERROR_UNEXPECTED_PAYLOAD = 2;
    ERROR_GENERIC = 3;
    ERROR_DECODE = 4;
    // register (1x)
    ERROR_WRONG_AGENT_ADDRESS = 10;
    ERROR_WRONG_PUBLIC_KEY = 11;
    ERROR_INVALID_PROOF = 12;
    ERROR_UNSUPPORTED_LEDGER = 13;
    // lookup & delivery (2x) 
    ERROR_UNKNOWN_AGENT_ADDRESS = 20;
    ERROR_AGENT_NOT_READY = 21;
  }
  StatusCodeEnum code = 1;
  repeated string msgs = 2;
...
---
initiation: [register, lookup_request, aea_envelope]
reply:
  register: [status]
  lookup_request: [lookup_response, status]
  aea_envelope: [status]
  status: []
  lookup_response: []
termination: [status, lookup_response]
roles: {node}
end_states: [successful, failed]
keep_terminal_state_dialogues: false
...
```

## Links
