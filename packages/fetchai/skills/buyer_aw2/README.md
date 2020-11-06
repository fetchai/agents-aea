# Car Park Client

## Description

This skill purchases information from other agents as specified in its configuration.

This skill finds an agent on the SOEF which sells the sought data in a vicinity, requests this data, negotiates the price, pays the proposed amount if agreement is reach, and receives the data bought.


## Behaviours

* search: searches for data selling service on SOEF

## Handlers

* fipa: handles fipa messages for negotiation
* ledger_api: handles ledger_api messages for payment
* oef_search: handles oef_search messages to manage the sellers it finds
* signing: handles signing messages for transaction signing by the decision maker


## Models

* strategy: allows the configuration of the purchasing. In particular, `location` and `search_radius` determines the vicinity in which the service is sought, `search_query` specifies the query, and the remaining coniguration allows determining the terms of trade.
