# Simple Oracle Client

## Description

This skill is used to deploy an oracle client smart contract to a ledger, approve the contract to make FET payments on behalf of the agent, and periodically call the contract function that requests the oracle value.

## Behaviours

* `simple_oracle_client_behaviour`: deploys oracle client contract, approves contract transactions, and calls the contract to request the oracle value every `tick_interval` seconds, as specified in the skill configuration.

## Handlers

* `contract_api`: handles `contract_api` messages for interactions with the smart contract
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `signing`: handles `signing` messages for transaction signing by the decision maker