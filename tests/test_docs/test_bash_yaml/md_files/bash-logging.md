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
- fetchai/stub:0.13.0
contracts: []
protocols:
- fetchai/default:0.10.0
skills:
- fetchai/error:0.10.0
default_connection: fetchai/stub:0.13.0
default_ledger: fetchai
logging_config:
  disable_existing_loggers: false
  version: 1
private_key_paths: {}
registry_path: ../packages
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
