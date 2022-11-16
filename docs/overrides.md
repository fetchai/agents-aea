## Component overrides

### Defining overrides

Component overrides are defined at a top level which has the package as a dependency. For example connection A is a dependency for skill that you developed and you want the connection to work with a different parameters but it's really not a good idea to update the configuration parameters for a third party package and this is where overrides are helpful. You can define an override section in configuration file of the skill. Continuing the example assume this is configuration file for connection A  

```yaml
name: connection_a
author: open_aea
version: 0.1.0
type: connection
description: Connection A.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
fingerprint:
  __init__.py: bafybeidmifvya6yjc6h7xppntnwqji2crm5o74xrwhmkutycdo4cqdryhy
  connection.py: bafybeigqfexwzamkgssmesfglbtnd3fstlwbsaveerzfezoipmkkk7ceke
  readme.md: bafybeihg5yfzgqvg5ngy7r2o5tfeqnelx2ffxw4po5hmheqjfhumpmxpoq
fingerprint_ignore_patterns: []
connections: []
protocols: []
class_name: MyScaffoldAsyncConnection
config:
  foo: bar
excluded_protocols: []
restricted_to_protocols: []
dependencies: {}
is_abstract: false
cert_requests: []
```

> The connection configuration only allows the `config` parameter to be updated so make sure to define every overridable parameter under the `config` section. 

and you want to update the config parameter `foo` to some other value. To do this define the override section in the skill configuration like this

```yaml
name: some_skill
author: open_aea
version: 0.1.0
type: skill
description: Some skill
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
fingerprint:
  __init__.py: bafybeiaxeinf2klacqlcz5gjki7lg5pefrwtcpzymq7uutcjyltrjzywm4
  behaviours.py: bafybeigvoskmq3cx6vyry7u6wnvrllnxco4ilwbrvflhua6xrbusqfrwi4
  handlers.py: bafybeih4cdyqerm6jji253tvqof3mgjnsb3eammnab6c2oekt4pfxy2qqe
  my_model.py: bafybeih447pl7wbcnrhjfbpt2cplyfs7jo4c37ocq3rd6yowc645arf5sm
fingerprint_ignore_patterns: []
connections: []
contracts: []
protocols: []
skills: []
behaviours:
  scaffold:
    args:
      foo: bar
    class_name: MyScaffoldBehaviour
handlers:
  scaffold:
    args:
      foo: bar
    class_name: MyScaffoldHandler
models:
  scaffold:
    args:
      foo: bar
    class_name: MyModel
dependencies: {}
is_abstract: false
---
public_id: valory/connection_a:0.1.0
type: connection
config:
  foo: some_other_value
```

When loading the skill, the loader will apply these overrides to the in-memory connection configuration, which means the original connection configuration won't be affected by the overrides.

> Although it's possible to perform overrides at the component level, avoid performing overrides at the component level. Use agent configuration to perform overrides. This will help you keep the configurations clean.

### Environment overrides

The configuration loader also allows the users to define overrides who's values can be picked up from the environment at the runtime. Define an environment override using following syntax

```yaml
some_parameter: ${ENVIRONMENT_VARIABLE_NAME:data_type:default_value}
```

- `ENVIRONMENT_VARIABLE_NAME` is a string representing the name of the environment variable to look for. Make sure it's all in the capital letters.
- `data_type` is a string defining the type of environment variable and needs to be one of the (`bool`, `int`, `float`, `str`, `list`, `dict`).
- `default_value` should be the default value to be used if the environment variable is not provided.

To use the environment variable placeholder on the example above, define `skill.yaml` like this

```yaml
name: some_skill
...
is_abstract: false
---
public_id: valory/connection_a:0.1.0
type: connection
config:
  foo: ${FOO:str:bar}
```

To utilise the environment variable placeholder, export the variable before running the application and make sure to use `--aev` flag if applicable for the given command

```
$ export FOO=some_other_value
$ aea run --aev
```

The environment variable loading mechanism also supports the auto generation of the environment variable name from the `json` path if the variable name is not provided by default. The auto generated environment variable follows `{COMPONENT_TYPE}_{COMPONENT_NAME}_{JSON_PATH}` format to generate variable names

Let's take following override as an example

```yaml
name: some_skill
...
is_abstract: false
---
public_id: valory/connection_a:0.1.0
type: connection
config:
  foo: ${str:bar}
```

Here we haven't define a environment variable name for the placeholder, this means when checking for the value the loading mechanism will generate the environment variable name for `foo` using it's `json` path. If we follow the format above, the environment variable name should be `CONNECTION_CONNECTION_A_CONFIG_FOO`

### Best practices when using overrides and suggestions 

- You can utilise environment overrides to avoid exposing private API keys in the public code.
- When defining network parameters like API endpoints and URLs, if you have a local server setup for the said API or URL use the local setting in the base component config and use overrides at the skill or agent level to utilise the production servers.
- Avoid defining environment placeholders in multiple configuration files, either define them at the base component configuration or at the top level configurations like a skill or an agent package.

### Default package overridables

- `Skill` package allows performing overrides on `args` sub parameter of the `handlers`, `behaviours`, `models` parameters.
- `Connection` package allows performing overrides on the `config`, `cert_requests`, `is_abstract`, `build_directory` parameters
- `Protocol` package does not allow any overrides
- `Contract` package allows performing overrides on the `build_directory` parameter
- `Agent` package allows performing overrides on `logging_config`, `private_key_paths`, `connection_private_key_paths`, `loop_mode`, `runtime_mode`, `task_manager_mode`, `execution_timeout`, `timeout`, `period`, `max_reactions`, `skill_exception_policy`, `connection_exception_policy`, `default_connection`, `default_ledger`, `required_ledgers`, `default_routing`, `storage_uri` parameters.