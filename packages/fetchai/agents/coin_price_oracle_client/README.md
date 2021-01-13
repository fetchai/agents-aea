# Coin Price Oracle Client AEA

An agent that deploys an oracle client contract that can request a coin price from an oracle contract.

## Description

This agent uses the `fetchai/simple_oracle_client` skill to deploy an oracle client smart contract to a ledger and periodically calls the contract function that requests the latest value of a coin price from a deployed oracle smart contract.

