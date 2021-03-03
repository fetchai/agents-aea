# Simple Seller

## Description

This skill is used to sell data present in the shared state.

## Behaviours

* `service_registration`: registers data selling service on the sOEF

## Handlers

* `fipa`: handles `fipa` messages for negotiation
* `ledger_api`: handles `ledger_api` messages for interacting with a ledger
* `oef_search`: handles `oef_search` messages if service registration on the sOEF is unsuccessful

## Models

* the `strategy` model is extended from the `fetchai/generic_seller` skill and loads data from the shared state using the key `shared_state_key` specified in the skill configuration.
