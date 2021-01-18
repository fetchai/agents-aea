# Oracle Protocol

## Description

This is a protocol for oracle networks.

## Specification

```yaml
---
name: consensus
author: fetchai
version: 0.1.0
description: A protocol for agents to aggregate individual observations
license: Apache-2.0
aea_version: '>=0.8.0, <0.9.0'
speech_acts:
  value:
    value: ct:Value
    signature: ct:SignedValue
  aggregated_value:
    value: ct:Value
    signature: ct:MultiSignedValue
...
---
ct:Value:
  bytes value = 1;
ct:SignedValue:
  bytes signed_value = 1;
ct:MultiSignedValue:
  bytes multi_signed_value = 1;
...
---
initiation: [value, aggregated_value]
reply:
  value: [value]
  aggregated_value: [aggregated_value]
termination: [value, raw_transaction, raw_message, error]
roles: {agent, ledger}
end_states: [successful, failed]
keep_terminal_state_dialogues: false
...
```

## Links
