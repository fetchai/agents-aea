# Car Park Detection

## Description

This skill sells information on the number of car parking spaces available in a given vicinity.

This skill is part of the Fetch.ai car park demo. It registers the "car park availability selling service" on the sOEF. It can be requested (for example by an agent with the `carpark_client` skill) to provide its data. It then negotiates the price and delivers the data after it receives payment.

## Behaviours

* `service_registration`: registers car park info selling service on the sOEF 

## Handlers

* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages if service registration on the sOEF is unsuccessful

## Links

* <a href="https://docs.fetch.ai/aea/car-park-skills/" target="_blank">Car Park Demo</a>
