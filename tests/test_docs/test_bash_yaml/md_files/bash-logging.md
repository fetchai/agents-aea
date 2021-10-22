``` bash
aea create my_aea
cd my_aea
```
``` yaml
agent_name: my_aea
author: fetchai
version: 0.1.0
description: ''
license: Apache-2.0
aea_version: 0.6.0
fingerprint: {}
fingerprint_ignore_patterns: []
connections:
- fetchai/stub:0.21.0
contracts: []
protocols:
- fetchai/default:1.0.0
skills:
- fetchai/error:0.17.0
default_connection: fetchai/stub:0.21.0
default_ledger: fetchai
required_ledgers:
- fetchai
logging_config:
  disable_existing_loggers: false
  version: 1
private_key_paths: {}
```
``` yaml
logging_config:
  version: 1
  disable_existing_loggers: False
  formatters:
    standard:
      format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  handlers:
    logfile:
      class: logging.FileHandler
      formatter: standard
      level: DEBUG
      filename: logconfig.log
    console:
      class: logging.StreamHandler
      formatter: standard
      level: DEBUG
  loggers:
    aea:
      handlers:
      - logfile
      - console
      level: DEBUG
      propagate: False
```
``` yaml
logging_config:
  version: 1
  disable_existing_loggers: false
  formatters:
    standard:
      format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  handlers:
    http:
      class: logging.handlers.HTTPHandler
      formatter: standard
      level: INFO
      host: localhost:5000
      url: /stream
      method: POST
  loggers:
    aea:
      handlers:
      - http
      level: INFO
      propagate: false
```
