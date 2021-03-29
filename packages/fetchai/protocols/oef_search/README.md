# OEF Search Protocol

## Description

This is a protocol for interacting with an OEF search service.
It allows for registering of agents and services, and searching of agents and services using a query language.

## Specification

```yaml
---
name: oef_search
author: fetchai
version: 1.0.0
description: A protocol for interacting with an OEF search service.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: fetchai/oef_search:1.0.0
speech_acts:
  register_service:
    service_description: ct:Description
  unregister_service:
    service_description: ct:Description
  search_services:
    query: ct:Query
  search_result:
    agents: pt:list[pt:str]
    agents_info: ct:AgentsInfo
  success:
    agents_info: ct:AgentsInfo
  oef_error:
    oef_error_operation: ct:OefErrorOperation
...
---
ct:Query: |
  bytes query_bytes = 1;
ct:Description: |
  bytes description_bytes = 1;
ct:AgentsInfo: |
  bytes agents_info = 1;
ct:OefErrorOperation: |
  enum OefErrorEnum {
        REGISTER_SERVICE = 0;
        UNREGISTER_SERVICE = 1;
        SEARCH_SERVICES = 2;
        SEND_MESSAGE = 3;
      }
  OefErrorEnum oef_error = 1;
...
---
initiation: [register_service, unregister_service, search_services]
reply:
  register_service: [success, oef_error]
  unregister_service: [success, oef_error]
  search_services: [search_result, oef_error]
  search_result: []
  oef_error: []
  success: []
termination: [oef_error, search_result, success]
roles: {agent, oef_node}
end_states: [successful, failed]
keep_terminal_state_dialogues: false
...
```

## Links
