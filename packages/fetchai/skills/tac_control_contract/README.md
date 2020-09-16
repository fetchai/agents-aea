# TAC Control Contract

## Description

This is the skill for managing a smart contract-based TAC.

This skill is part of the Fetch.ai TAC demo. It manages the smart contract (contract deployment, creating tokens, minting tokens) and manages the progression of the competition along its various stages.

## Behaviours

* contract: manages the contract (deploying the contract, creating tokens, minting tokens) 
* tac:  deploys smart contract, manages progression of the competition

## Handlers

* tac: handles TAC messages for registering/unregistering agents in the TAC
* oef: handles oef_search messages if (un)registration on SOEF is unsuccessful
* transaction: handles signing messages for communication with the ledger

## Links

* <a href="https://docs.fetch.ai/aea/tac-skills-contract/" target="_blank">TAC Demo</a>
