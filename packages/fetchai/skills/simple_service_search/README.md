# Simple Service Search

## Description

This skill searches for services on the sOEF.

## Behaviours

* `service_search`: sends search queries to the sOEF using the `oef_search` protocol. 

## Handlers

* `oef_search`: handles `oef_search` messages, in particular search responses. Search results are stored in the shared state using the key `shared_storage_key`.

## Models

* `strategy`: builds the search query from the data provided in the skill configuration: `search_location`, `search_query` and `search_radius`.
