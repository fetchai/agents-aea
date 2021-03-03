# Thermometer Client

## Description

This skill buys thermometer data.

This skill is part of the Fetch.ai thermometer demo. It finds an agent which sells thermometer data, requests data from a reading and pays the proposed amount.

## Behaviours

* `search`: searches for thermometer data selling service on the sOEF
* `transaction`: sequentially processes transactions' settlements on a blockchain

## Handlers

* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages to manage the sellers found
* `signing`: handles `signing` messages for transaction signing by the decision maker


## Links

* <a href="https://docs.fetch.ai/aea/thermometer-skills/" target="_blank">Thermometer Demo</a>
