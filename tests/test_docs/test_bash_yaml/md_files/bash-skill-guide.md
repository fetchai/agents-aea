``` bash
aea create my_aea && cd my_aea
aea scaffold skill my_search
```
``` yaml
name: my_search
author: fetchai
version: 0.1.0
license: Apache-2.0
description: 'A simple search skill utilising the OEF search and communication node.'
fingerprint: ''
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
protocols: ['fetchai/oef_search:0.1.0']
dependencies: {}
```
``` bash
aea add protocol fetchai/oef_search:0.1.0
```
``` bash
aea add connection fetchai/oef:0.1.0
aea install
```
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` yaml
name: simple_service_registration
author: fetchai
version: 0.1.0
license: Apache-2.0
description: The scaffold skill is a scaffold for your own skill implementation.
fingerprint: ''
behaviours:
  service:
    args:
      services_interval: 30
    class_name: ServiceRegistrationBehaviour
handlers: {}
models:
  strategy:
    class_name: Strategy
    args:
      data_model_name: location
      data_model:
        attribute_one:
          name: country
          type: str
          is_required: True
        attribute_two:
          name: city
          type: str
          is_required: True
      service_data:
        country: UK
        city: Cambridge
protocols: ['fetchai/oef_search:0.1.0']
dependencies: {}
```
```bash
aea run --connections fetchai/oef:0.1.0
```
