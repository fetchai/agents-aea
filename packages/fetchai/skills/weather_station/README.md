# Weather Station

## Description

This skill sells dummy weather data.

This skill is part of the Fetch.ai weather demo. It reads data from a database, that is populated with  dummy data from a weather station. It can be requested (for example by an agent with the `weather_client` skill) to provide weather data for specific dates, which it delivers after it receives payment.

## Behaviours

* `service_registration`: registers weather selling service on the sOEF

## Handlers

* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages if service registration on the sOEF is unsuccessful

## Links

* <a href="https://docs.fetch.ai/aea/weather-skills/" target="_blank">Weather Demo</a>
