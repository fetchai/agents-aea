# Weather Station

## Description

This skill sells dummy weather data.

This skill is part of a Fetch.ai weather demo. It reads data from a database, that is populated with  dummy data from a weather station. It can be requested (for example by an agent with the weather_client skill) to provide weather data for specific dates, which it delivers after it receives payment.

## Behaviours

* service_registration: registers service on soef search service 

## Handlers

* fipa: handles fipa messages for negotiation
* ledger_api: handles ledger_api messages for payment
* oef_search: handles oef_search messages if service registration on soef is unsuccessful

## Dependencies

### Contracts

### Protocols

- fetchai/default:0.5.0
- fetchai/fipa:0.6.0
- fetchai/ledger_api:0.3.0
- fetchai/oef_search:0.5.0

### Skills

- fetchai/generic_seller:0.11.0

## Links

* <a href="https://docs.fetch.ai/aea/weather-skills/" target="_blank">Weather Demo</a>