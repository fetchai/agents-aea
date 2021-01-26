# Car Park Client

## Description

This skill purchases information on available car parking spaces in a vicinity.

This skill finds an agent on the sOEF which sells car park availability data in a vicinity, requests this data, negotiates the price, pays the proposed amount if agreement is reach, and receives the data bought.


## Behaviours

* `search`: searches for car park data selling service on the sOEF
* `transaction`: sequentially processes transactions' settlements on a blockchain

## Handlers

* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages to manage the sellers found
* `signing`: handles `signing` messages for transaction signing by the decision maker


## Links

* <a href="https://docs.fetch.ai/aea/car-park-skills/" target="_blank">Car Park Demo</a>
