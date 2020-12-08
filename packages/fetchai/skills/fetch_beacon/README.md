# Fetch Beacon

## Description

This skill is used to get the latest value of the Fetch Decentralised Random Beacon (DRB).

## Behaviours

* fetch_beacon_behaviour: requests beacon value every `tick_interval` seconds from REST the endpoint `beacon_url` specified in the skill config.

## Handlers

* http: processes incoming HTTP messages, retrieves the beacon value from the appropriate response, and stores it in shared state under the key: `oracle_data`.
