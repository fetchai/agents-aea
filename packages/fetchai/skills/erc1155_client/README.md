# ERC1155 Client

## Description

This is a skill for demoing the purchase of data via a smart contract.

This skill finds an `ERC1155 contract deployment AEA` on the sOEF, requests specific data, negotiates the price, pays the proposed amount via smart contract if agreement is reach, and receives the data bought.


## Behaviours

* `search`: searches for the ERC1155 deployment agent on the sOEF

## Handlers

* `contract_api`: handles `contract_api` messages for interactions with the smart contract
* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages to manage the sellers found
* `signing`: handles `signing` messages for transaction signing by the decision maker


## Links

* <a href="https://docs.fetch.ai/aea/erc1155-skills/" target="_blank">Contract Deployment Guide</a>
