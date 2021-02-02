# Simple Oracle

## Description

This skill is used to deploy an oracle smart contract to a ledger, grant oracle permissions, and periodically update the oracle value in the contract.

## Behaviours

* `simple_oracle_behaviour`: deploys oracle contract, grants the oracle role to the agent address, and updates the oracle value every `tick_interval` seconds, as specified in the skill configuration.

## Handlers

* `contract_api`: handles `contract_api` messages for interactions with a smart contract
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `prometheus`: handles `prometheus` messages for interactions with a prometheus server
* `signing`: handles `signing` messages for transaction signing by the decision maker