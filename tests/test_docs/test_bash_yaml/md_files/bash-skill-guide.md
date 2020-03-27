``` bash
aea create my_aea && cd my_aea
aea scaffold skill my_search
```
``` yaml
name: my_search
author: fetchai
version: 0.1.0
license: Apache-2.0
aea_version: 0.2.4
description: 'A simple search skill utilising the OEF search and communication node.'
fingerprint: {}
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
aea fingerprint skill fetchai/my_search:0.1.0
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
fingerprint:
  __init__.py: QmNkZAetyctaZCUf6ACxP5onGWsSxu2hjSNoFmJ3ta6Lta
  behaviours.py: QmcYLWnWuB121Ghefv58GevCqAAetx1H7taMem94xwCjHQ
  data_model.py: QmagLM4fo1Eh6zfoePCA22mgVVzA34DAzKGyQV5ZABRSHa
  strategy.py: QmbZhUVuKbEmiBEP7mygarGJPSVu13WiqtrWKeypcKpLHZ
aea_version: 0.2.4
description: The simple service registration skills is a skill to register a service.
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
