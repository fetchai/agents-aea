# ERC1155 Deployer

An agent that deploys a smart contract sells data using it.

## Description

This agent uses its primary skill, the `fetchai/erc1155_deploy` skill, to deploy a smart contract, create and mint tokens, and register its 'data-selling' service on the `SOEF`. It can then be contacted by another agent (for example the `fetchai/erc1155_client` agent) to provide specific data. 

Once such a request is made, this agent negotiates the terms of trade using the `fetchai/fipa` protocol, and if an agreement is reached, it delivers the data after receiving payment via the deployed smart contract.

## Links

* <a href="https://docs.fetch.ai/aea/erc1155-skills/" target="_blank">Contract Deployment Guide</a>
