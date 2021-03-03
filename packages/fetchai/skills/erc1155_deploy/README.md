# ERC1155 Deploy

## Description

This is a skill for selling data via a smart contract.

This skill registers some data selling service on the sOEF. It can be requested (for example by an agent with the `generic_buyer` skill) to provide specific data. It then negotiates the price and delivers the data after it receives payment.

## Behaviours

* `service_registration`: Deploys the smart contract, creates and mints tokens, registers `ERC1155 data selling service` on the sOEF

## Handlers

* `contract_api`: handles `contract_api` messages for interactions with the smart contract
* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger.
* `oef_search`: handles `oef_search` messages if service registration on the sOEF is unsuccessful
* `signing`: handles `signing` messages for transaction signing by the decision maker

## Links

* <a href="https://docs.fetch.ai/aea/erc1155-skills/" target="_blank">Contract Deployment Guide</a>
