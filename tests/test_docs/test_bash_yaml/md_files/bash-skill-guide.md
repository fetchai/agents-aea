``` bash
aea create my_aea && cd my_aea
aea scaffold skill my_search
```
``` yaml
name: my_search
author: fetchai
version: 0.1.0
license: Apache-2.0
description: 'A simple search skill utilising the OEF.'
behaviours:
  my_search_behaviour:
    class_name: MySearchBehaviour
    args:
      tick_interval: 5
handlers:
  my_search_handler:
    class_name: MySearchHandler
    args: {}
models: {}
protocols: ['fetchai/oef:0.1.0']
dependencies: {}
```
``` bash
aea add protocol fetchai/oef:0.1.0
```
``` bash
aea add connection fetchai/oef:0.1.0
```
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
```bash
aea run --connections fetchai/oef:0.1.0
```
