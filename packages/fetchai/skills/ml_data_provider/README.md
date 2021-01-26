# ML Train Provider

## Description

This skill sells ML data for training.

This skill is part of the Fetch.ai ML skill demo. It registers its "ML data selling service" on the sOEF. It can be requested (for example by an agent with the `ml_train` skill) to provide specific data samples, which it delivers after it receives payment.

## Behaviours

* `service_registration`: registers service on the sOEF search service 

## Handlers

* `ml_trade`: handles `ml_trade` messages for negotiating the terms of trade
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages if service registration on the sOEF is unsuccessful

## Links

* <a href="https://docs.fetch.ai/aea/ml-skills/" target="_blank">ML Demo</a>
