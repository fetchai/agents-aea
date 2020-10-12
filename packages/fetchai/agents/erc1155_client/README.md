# ERC1155 Client

An agent that purchases data via a smart contract.

## Description

This agent uses its primary skill, the `fetchai/erc1155_client` skill, to find an agent selling data on the `SOEF` service.
 
 Once found, it requests specific data, negotiates the price using the `fetchai/fipa` protocol, and if an agreement is reached, pays the proposed amount via a deployed smart contract and receives the data.

## Links

* <a href="https://docs.fetch.ai/aea/erc1155-skills/" target="_blank">Contract Deployment Guide</a>
