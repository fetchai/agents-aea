# Fetch Beacon

## Description

This skill is used to get the latest value of the Fetch Decentralised Random Beacon (DRB).

## Behaviours

* `fetch_beacon_behaviour`: requests beacon value every `tick_interval` seconds from the REST endpoint `beacon_url` specified in the skill configuration.

## Handlers

* `http`: handles incoming `http` messages, retrieves the beacon value from the appropriate response, and stores it in shared state under the key: `oracle_data`.
