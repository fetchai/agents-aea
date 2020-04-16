``` bash
aea create my_aea
cd my_aea
```
``` yaml
aea_version: '>=0.3.0, <0.4.0'
agent_name: my_aea
author: ''
connections:
- fetchai/stub:0.2.0
default_connection: fetchai/stub:0.2.0
default_ledger: fetchai
description: ''
fingerprint: ''
ledger_apis: {}
license: ''
logging_config:
  disable_existing_loggers: false
  version: 1
private_key_paths: {}
protocols:
- fetchai/default:0.1.0
registry_path: ../packages
skills:
- fetchai/error:0.2.0
version: 0.1.0
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
