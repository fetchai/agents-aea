# Car Park Client

## Description

This skill purchases information on available car parking spaces in a vicinity.

This skill finds an agent on the SOEF which sells car park availability data in a vicinity, requests this data, negotiates the price, pays the proposed amount if agreement is reach, and receives the data bought.


## Behaviours

* search: searches for data selling service on SOEF

## Handlers

* fipa: handles fipa messages for negotiation
* ledger_api: handles ledger_api messages for payment
* oef_search: handles oef_search messages to manage the sellers it finds
* signing: handles signing messages for transaction signing by the decision maker


## Links

* <a href="https://docs.fetch.ai/aea/car-park-skills/" target="_blank">Car Park Demo</a>
