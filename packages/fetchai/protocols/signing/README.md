# Signing Protocol

## Description

This is a protocol for communication between a skill and a decision maker.

## Specification

```yaml
---
name: signing
author: fetchai
version: 1.0.0
description: A protocol for communication between skills and decision maker.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/signing:1.0.0
speech_acts:
  sign_transaction:
    terms: ct:Terms
    raw_transaction: ct:RawTransaction
  sign_message:
    terms: ct:Terms
    raw_message: ct:RawMessage
  signed_transaction:
    signed_transaction: ct:SignedTransaction
  signed_message:
    signed_message: ct:SignedMessage
  error:
    error_code: ct:ErrorCode
...
---
ct:ErrorCode: |
  enum ErrorCodeEnum {
      UNSUCCESSFUL_MESSAGE_SIGNING = 0;
      UNSUCCESSFUL_TRANSACTION_SIGNING = 1;
    }
  ErrorCodeEnum error_code = 1;
ct:RawMessage: |
  bytes raw_message = 1;
ct:RawTransaction: |
  bytes raw_transaction = 1;
ct:SignedMessage: |
  bytes signed_message = 1;
ct:SignedTransaction: |
  bytes signed_transaction = 1;
ct:Terms: |
  bytes terms = 1;
...
---
initiation: [sign_transaction, sign_message]
reply:
  sign_transaction: [signed_transaction, error]
  sign_message: [signed_message, error]
  signed_transaction: []
  signed_message: []
  error: []
termination: [signed_transaction, signed_message, error]
roles: {skill, decision_maker}
end_states: [successful, failed]
keep_terminal_state_dialogues: false
...
```

## Links
