# Ledger API Protocol

## Description

This is a protocol for interacting with ledger APIs.

## Specification

```yaml
---
name: ledger_api
author: fetchai
version: 1.0.0
description: A protocol for ledger APIs requests and responses.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/ledger_api:1.0.0
speech_acts:
  get_balance:
    ledger_id: pt:str
    address: pt:str
  get_raw_transaction:
    terms: ct:Terms
  send_signed_transaction:
    signed_transaction: ct:SignedTransaction
  get_transaction_receipt:
    transaction_digest: ct:TransactionDigest
  balance:
    ledger_id: pt:str
    balance: pt:int
  raw_transaction:
    raw_transaction: ct:RawTransaction
  transaction_digest:
    transaction_digest: ct:TransactionDigest
  transaction_receipt:
    transaction_receipt: ct:TransactionReceipt
  get_state:
    ledger_id: pt:str
    callable: pt:str
    args: pt:list[pt:str]
    kwargs: ct:Kwargs
  state:
    ledger_id: pt:str
    state: ct:State
  error:
    code: pt:int
    message: pt:optional[pt:str]
    data: pt:optional[pt:bytes]
...
---
ct:Terms: |
  bytes terms = 1;
ct:Kwargs: |
  bytes kwargs = 1;
ct:State: |
  bytes state = 1;
ct:SignedTransaction: |
  bytes signed_transaction = 1;
ct:RawTransaction: |
  bytes raw_transaction = 1;
ct:TransactionDigest: |
  bytes transaction_digest = 1;
ct:TransactionReceipt: |
  bytes transaction_receipt = 1;
...
---
initiation: [get_balance, get_state, get_raw_transaction, send_signed_transaction, get_transaction_receipt]
reply:
  get_balance: [balance, error]
  balance: []
  get_state: [state, error]
  state: []
  get_raw_transaction: [raw_transaction, error]
  raw_transaction: [send_signed_transaction]
  send_signed_transaction: [transaction_digest, error]
  transaction_digest: [get_transaction_receipt]
  get_transaction_receipt: [transaction_receipt, error]
  transaction_receipt: []
  error: []
termination: [balance, state, transaction_receipt, error]
roles: {agent, ledger}
end_states: [successful]
keep_terminal_state_dialogues: false
...
```

## Links
