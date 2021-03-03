# Weather Client

## Description

This skill buys dummy weather data.

This skill is part of the Fetch.ai weather demo. It finds an agent which sells weather data, requests data for specific dates and pays the proposed amount.

## Behaviours

* `search`: searches for weather data selling service on the sOEF
* `transaction`: sequentially processes transactions' settlements on a blockchain

## Handlers

* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages to manage the sellers found
* `signing`: handles `signing` messages for transaction signing by the decision maker


## Links

* <a href="https://docs.fetch.ai/aea/weather-skills/" target="_blank">Weather Demo</a>