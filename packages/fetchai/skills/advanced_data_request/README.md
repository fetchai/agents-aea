# Advanced Data Request

## Description

This skill is used to get specific data from an API, which can either be shared with other agent skills or made available by http request.

## Behaviours

* `advanced_data_request_behaviour`: requests data from specified source every `tick_interval` seconds from the API endpoint `url` specified in the skill configuration.

## Handlers

* `http`: handles incoming `http` messages, retrieves the data from the appropriate response, stores it in shared state under the key: `observation`, and responds to requests satisfying the API specification listed in `api_spec.yaml`.
