# Simple Data Request

## Description

This skill is used to request data from a HTTP endpoint and then save it in the AEA's shared state for use by other skills.

## Behaviours

* `http_request`: requests data every `request_interval` seconds from a HTTP endpoint using the `url`, `method` and `body` specified in the skill configuration.

## Handlers

* `http`: handles incoming `http` messages. Data received in responses is saved in the shared state using the key specified in the skill configuration: `shared_state_key`.
