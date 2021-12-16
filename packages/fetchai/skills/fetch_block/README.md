# Fetch Block

## Description

This skill is used to get the latest block data from the Fetch ledger.

## Behaviours

* `fetch_block_behaviour`: requests latest block data every `tick_interval` seconds from the REST endpoint for the FetchAI ledger.

## Handlers

* `http`: handles incoming `http` messages, retrieves the block data from the appropriate response, and stores it in shared state under the key: `block_data`.
