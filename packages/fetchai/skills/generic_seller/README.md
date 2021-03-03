# Generic Seller

## Description

This is a generic skill for selling data.

This skill registers some data selling service on the sOEF. It can be requested (for example by an agent with the `generic_buyer` skill) to provide specific data. It then negotiates the price and delivers the data after it receives payment.

## Behaviours

* `service_registration`: registers data selling service on the sOEF 

## Handlers

* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages if service registration on the sOEF is unsuccessful

## Links

* <a href="https://docs.fetch.ai/aea/generic-skills/" target="_blank">Generic Skills</a>
* <a href="https://docs.fetch.ai/aea/generic-skills-step-by-step/" target="_blank">Generic Skill Step by Step Guide</a>
