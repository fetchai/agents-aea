# Confirmation AW3

## Description

This skill purchases information from other agents as specified in its configuration. It acts as the confirmation AEA in Agent World 3.

This skill searches for an agent in a vicinity on the sOEF that sells the data this skill is configured to buy. Once it found some agents which match Agent World 3 criteria, it requests this data, negotiates the price, pays the proposed amount if agreement is reached, and receives the data bought. The skill just randomly selects the location in which it searches and the query from a list. On each search it completes as many trade as possible.


## Behaviours

* `search`: searches for data selling service on the sOEF
* `transaction`: sequentially processes transactions' settlements on a blockchain

## Handlers

* `default`: handles `default` messages for registration
* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages to manage the sellers found
* `signing`: handles `signing` messages for transaction signing by the decision maker


## Models

* `strategy`: allows the configuration of the purchasing. In particular, location and `search_radius` together determine the vicinity where the service is searched for, `search_query` specifies the query, and the remaining configuration specifies the terms of trade. Also, rules regarding Agent World 3 are enforced.
