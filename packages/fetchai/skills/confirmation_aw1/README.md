# Confirmation AW1

## Description

The `confirmation_aw1` skill is for handling registrations in Agent World 1.

## Behaviours

* `transaction`: sequentially processes transactions' settlements on a blockchain 

## Handlers

* `contract_api`: handles `contract_api` messages for communication with a staking contract
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `registration`: handles `register` messages for registration requests
* `signing`: handles `signing` messages for transaction signing by the decision maker

## Models

* `strategy`: contains the confirmation configuration
