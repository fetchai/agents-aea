# Generic Buyer

## Description

This is a generic skill for buying data.

This skill finds an agent on the SOEF which sells data, requests specific data, negotiates the price, pays the proposed amount if agreement is reach, and receives the data bought.


## Behaviours

* search: searches for data selling service on SOEF

## Handlers

* fipa: handles fipa messages for negotiation
* ledger_api: handles ledger_api messages for payment
* oef_search: handles oef_search messages to manage the sellers it finds
* signing: handles signing messages for transaction signing by the decision maker


## Links

* <a href="https://docs.fetch.ai/aea/generic-skills/" target="_blank">Generic Skills</a>
* <a href="https://docs.fetch.ai/aea/generic-skills-step-by-step/" target="_blank">Generic Skill Step by Step Guide</a>
