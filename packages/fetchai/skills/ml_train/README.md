# ML Train

## Description

This skill buys ML data for training.

This skill is part of the Fetch.ai ML skill demo. It finds an agent which sells ML data, requests data and pays the proposed amount. Then trains an ML model using the bought data.

## Behaviours

* search: searches for ML data selling service on soef 

## Handlers

* ml_trade: handles ml_trade messages for negotiating the terms of trade
* ledger_api: handles ledger_api messages for payment
* oef_search: handles oef_search messages to manage the sellers it finds
* signing: handles signing messages for transaction signing by the decision maker


## Links

* <a href="https://docs.fetch.ai/aea/ml-skills/" target="_blank">ML Demo</a>