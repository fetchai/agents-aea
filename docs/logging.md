The AEA framework supports flexible logging capabilities with the standard [Python logging library](https://docs.python.org/3/library/logging.html).

In this tutorial, we will configure logging for an agent.

First of all, create your agent:


``` bash
aea create my_agent
cd my_agent
```

The `aea-config.yaml` file should look like:
```yaml
aea_version: 0.1.6
agent_name: my_agent
authors: ''
connections:
- oef
default_connection: oef
license: ''
private_key_pem_path: ''
protocols:
- default
registry_path: ../packages
skills:
- error
url: ''
version: v1
logging_config:
  disable_existing_loggers: false
  version: 1
```

By updating the `logging_config` section, you can configure 
the loggers of your application.

The format of this section is specified in the 
[`logging.config`](https://docs.python.org/3/library/logging.config.html)
module.
At [this section](https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema) 
you'll find the definition of the configuration dictionary schema.

An example of `logging_config` value is reported below:

```yaml
logging_config:
  version: 1
  disable_existing_loggers: false
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
      propagate: true
```

This configuration will set up a logger with name `aea`,
print both on console (see `console` handler) and on file
(see `logfile` handler) with format specified by the 
`standard` formatter.


<br />