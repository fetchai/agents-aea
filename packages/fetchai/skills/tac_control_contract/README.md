# TAC Control Contract

## Description

This is the skill for managing a smart contract-based TAC.

This skill is part of the Fetch.ai TAC demo. It manages the smart contract (contract deployment, creating tokens, minting tokens) and manages the progression of the competition along its various stages.

## Behaviours

* tac:  deploys smart contract, manages progression of the competition

## Handlers

* contract_api: handles contract_api messages for interaction with contract
* ledger_api: handles ledger_api messages for interaction with ledger
* oef: handles oef_search messages if (un)registration on SOEF is unsuccessful
* signing: handles signing messages for interaction with decision maker
* tac: handles TAC messages for registering/unregistering agents in the TAC

## Links

* <a href="https://docs.fetch.ai/aea/tac-skills-contract/" target="_blank">TAC Demo</a>
