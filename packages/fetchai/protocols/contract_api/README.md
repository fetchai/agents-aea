# Contract API Protocol

## Description

This is a protocol for contract APIs' requests and responses.

## Specification

```yaml
---
name: contract_api
author: fetchai
version: 1.0.0
description: A protocol for contract APIs requests and responses.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/contract_api:1.0.0
speech_acts:
  get_deploy_transaction:
    ledger_id: pt:str
    contract_id: pt:str
    callable: pt:str
    kwargs: ct:Kwargs
  get_raw_transaction:
    ledger_id: pt:str
    contract_id: pt:str
    contract_address: pt:str
    callable: pt:str
    kwargs: ct:Kwargs
  get_raw_message:
    ledger_id: pt:str
    contract_id: pt:str
    contract_address: pt:str
    callable: pt:str
    kwargs: ct:Kwargs
  get_state:
    ledger_id: pt:str
    contract_id: pt:str
    contract_address: pt:str
    callable: pt:str
    kwargs: ct:Kwargs
  state:
    state: ct:State
  raw_transaction:
    raw_transaction: ct:RawTransaction
  raw_message:
    raw_message: ct:RawMessage
  error:
    code: pt:optional[pt:int]
    message: pt:optional[pt:str]
    data: pt:bytes
...
---
ct:Kwargs:
  bytes kwargs = 1;
ct:State:
  bytes state = 1;
ct:RawTransaction:
  bytes raw_transaction = 1;
ct:RawMessage:
  bytes raw_message = 1;
...
---
initiation: [get_deploy_transaction, get_raw_transaction, get_raw_message, get_state]
reply:
  get_deploy_transaction: [raw_transaction, error]
  get_raw_transaction: [raw_transaction, error]
  get_raw_message: [raw_message, error]
  get_state: [state, error]
  raw_transaction: []
  raw_message: []
  state: []
  error: []
termination: [state, raw_transaction, raw_message, error]
roles: {agent, ledger}
end_states: [successful, failed]
keep_terminal_state_dialogues: false
...
```

## Links
