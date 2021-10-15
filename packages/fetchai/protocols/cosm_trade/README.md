# Ledger API Protocol

## Description

This is a protocol for preparing an atomic swap bilateral transaction for cosmos-based ledgers, including fetchai's. 
For two parties A and B to atomically swap tokens on cosmos-based networks, A has to send its public key to B.
Then B constructs the transaction using both his public key and A's, signs the transaction, adds its signature to the list of signatures in the transaction and sends this to A. 
After receiving, A signs the transaction, adds its signature to the list of signatures in the transaction and broadcasts it to the network for processing.

## Specification

```yaml
---
name: cosm_trade
author: fetchai
version: 0.1.0
description: A protocol for preparing an atomic swap bilateral transaction for cosmos-based ledgers, including fetchai's.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/cosm_trade:1.0.0
speech_acts:
  inform_public_key:
    public_key: pt:str
  inform_signed_transaction:
    signed_transaction: ct:SignedTransaction
    fipa_dialogue_id: pt:optional[pt:list[pt:str]]
  error:
    code: pt:int
    message: pt:optional[pt:str]
    data: pt:optional[pt:bytes]
  end: {}
...
---
ct:SignedTransaction: |
  bytes signed_transaction = 1;
...
---
initiation: [inform_public_key, inform_signed_transaction]
reply:
  inform_public_key: [inform_signed_transaction, error]
  inform_signed_transaction: [error, end]
  error: []
  end: []
termination: [error, end]
roles: {agent}
end_states: [successful, failed]
keep_terminal_state_dialogues: false
...
```

## Links
