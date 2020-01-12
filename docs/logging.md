The AEA framework supports flexible logging capabilities with the standard <a href="https://docs.python.org/3/library/logging.html" target=_blank>Python logging library</a>.

In this tutorial, we configure logging for an agent.

First of all, create your agent.


``` bash
aea create my_agent
cd my_agent
```

The `aea-config.yaml` file should look like this.

``` yaml
aea_version: 0.1.16
agent_name: my_agent
author: ''
connections:
- fetchai/stub:0.1.0
default_connection: fetchai/stub:0.1.0
default_ledger: fetchai
description: ''
fingerprint: ''
ledger_apis: {}
license: ''
logging_config:
  disable_existing_loggers: false
  version: 1
private_key_paths: []
protocols:
- fetchai/default:0.1.0
registry_path: ../packages
skills:
- fetchai/error:0.1.0
version: 0.1.0
```

By updating the `logging_config` section, you can configure the loggers of your application.

The format of this section is specified in the <a href="https://docs.python.org/3/library/logging.config.html" target=_blank>`logging.config`</a> module.

At <a href="https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema" target=_blank>this section</a> 
you'll find the definition of the configuration dictionary schema.

Below is an example of the `logging_config` value.

```yaml
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
      propagate: True
```

This configuration will set up a logger with name `aea`. It prints both on console and on file with a format specified by the `standard` formatter.


<br />