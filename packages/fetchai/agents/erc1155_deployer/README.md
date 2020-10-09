# ERC1155 Deployer

This is an agent that sells data via a smart contract.

## Description

This agent uses its primary skill, the `fetchai/erc1155_deploy` skill, to register its 'data-selling' service on the `SOEF`. It can then be contacted by another agent (for example the `fetchai/generic_buyer` agent) to provide specific data. Once such aa request is made, this agent negotiates the terms of a deal using the `fetchai/fipa` protocol, and if an agreement is reached, it delivers the data after receiving payment via its deployed smart contract.

## Links

* <a href="https://docs.fetch.ai/aea/erc1155-skills/" target="_blank">Contract Deployment Guide</a>
