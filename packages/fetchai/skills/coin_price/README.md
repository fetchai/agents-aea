# Coin Price

## Description

This skill is used to get the latest coin or token price from an API, which can either be shared with other agent skills or made available by http request.

## Behaviours

* coin_price_behaviour: requests coin price of `coin_id` in currency `currency` every `tick_interval` seconds from the API endpoint `url` specified in the skill config.

## Handlers

<<<<<<< HEAD
* http: processes incoming HTTP messages, retrieves the coin price from the appropriate response, stores it in shared state under the key: `oracle_data`, and responds to requests meeting the API specification listed in `coin_api_spec.yaml`.
=======
* http: processes incoming HTTP messages, retrieves the coin price from the appropriate response, stores it in shared state under the key: `oracle_data`, and responds to requests meeting the API specification listed in `coin_api_spec.yaml`.
>>>>>>> 446ab76c68ad72b8e6dd29f9702d4c67237cbdcb
