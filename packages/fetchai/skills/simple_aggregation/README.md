# Simple Aggregation

## Description

This skill is used to find peers on the agent communication network, exchange observations of some real-world quantity, and periodically aggregate the collected observations.

## Behaviours

* `search_behaviour`: searches for other aggregating peers every `search_interval` seconds, as specified in the skill configuration.
* `aggregation_behaviour`: makes observations and aggregates those received from peers every `aggregation_interval` seconds, as specified in the skill configuration.

## Handlers

* `aggregation`: handles `aggregation` messages to and from peers
* `oef_search`: handles `oef_search` messages for interacting with the SOEF
