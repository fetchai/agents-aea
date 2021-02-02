# Thermometer

## Description

This skill sells thermometer data.

This skill is part of the Fetch.ai thermometer demo. It can be requested (for example by an agent with the `thermometer_client` skill) to provide thermometer data. If agreement is reached on the price via negotiation, it reads data from a (real or fake) thermometer, then delivers it after receiving payment.

## Behaviours

* `service_registration`: registers thermometer data selling service on the sOEF 

## Handlers

* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages if service registration on the sOEF is unsuccessful

## Links

* <a href="https://docs.fetch.ai/aea/thermometer-skills/" target="_blank">Thermometer Demo</a>
