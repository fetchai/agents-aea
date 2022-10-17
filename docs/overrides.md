## Component overrides

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

Although it's possible to perform overrides at the component level, avoid performing overrides at the component level. Use agent configuration to perform overrides. This will help you keep the configurations clean.