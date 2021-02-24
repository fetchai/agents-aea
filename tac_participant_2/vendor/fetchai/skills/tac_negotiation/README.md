# TAC Negotiation

## Description

This is the skill for negotiation in a TAC.

This skill is part of the Fetch.ai TAC demo. It manages registration and searching of agents and services on the sOEF and negotiations of goods with other agents.

## Behaviours

* `clean_up`: updates and cleans up confirmed and pending transactions 
* `tac_negotiation`: registers/unregisters the agent and its buying/selling services on the sOEF 

## Handlers

* `contract_api`: handles `contract_api` messages for interaction with a smart contract
* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef`: handles `oef_search` messages to manage the buyers/sellers it finds
* `signing`: handles `signing` messages for transaction signing by the decision maker

## Links

* <a href="https://docs.fetch.ai/aea/tac-skills-contract/" target="_blank">TAC Demo</a>
