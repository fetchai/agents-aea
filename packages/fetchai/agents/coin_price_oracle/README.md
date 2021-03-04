# Coin Price Oracle AEA

An agent that fetches a coin price from an API and makes it available by request to an oracle smart contract. 

## Description

This agent uses the `fetchai/simple_oracle` skill to deploy an oracle smart contract to a ledger and updates this contract with the latest value of a coin price fetched using the `fetchai/advanced_data_request` skill.

