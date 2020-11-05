# Ledger API Protocol

## Description

This is a protocol for interacting with ledger APIs.

## Specification

```yaml
---
name: ledger_api
author: fetchai
version: 0.7.0
description: A protocol for ledger APIs requests and responses.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
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
  error:
    code: pt:int
    message: pt:optional[pt:str]
    data: pt:optional[pt:bytes]
...
---
ct:Terms: |
  bytes terms = 1;
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
initiation: [get_balance, get_raw_transaction, send_signed_transaction, get_transaction_receipt]
reply:
  get_balance: [balance, error]
  balance: []
  get_raw_transaction: [raw_transaction, error]
  raw_transaction: [send_signed_transaction]
  send_signed_transaction: [transaction_digest, error]
  transaction_digest: [get_transaction_receipt]
  get_transaction_receipt: [transaction_receipt, error]
  transaction_receipt: []
  error: []
termination: [balance, transaction_receipt]
roles: {agent, ledger}
end_states: [successful]
...
```

## Links
