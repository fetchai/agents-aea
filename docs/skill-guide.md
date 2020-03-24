<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>Before developing your first skill, please read the <a href="../skill/">skill guide</a>.</p>
</div>

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Step 1: Setup

We will first create an AEA and add a scaffold skill, which we call `my_search`.

``` bash
aea create my_aea && cd my_aea
aea scaffold skill my_search
```

In the following steps, we replace the scaffolded `Behaviour` and `Handler` in `my_aea/skills/my_search` with our implementation. We will build a simple skill which lets the AEA send a search query to the [OEF search node](../oef-ledger) and process the resulting response.

## Step 2: Develop a Behaviour

A `Behaviour` class contains the business logic specific to initial actions initiated by the AEA rather than reactions to other events.

In this example, we implement a simple search behaviour. Each time, `act()` gets called by the main agent loop, we will send a search request to the [OEF search node](../oef-ledger) via the [OEF communication network](../oef-ledger).

``` python
from aea.helpers.search.models import Constraint, ConstraintType, Query
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.oef_search.serialization import OefSearchSerializer


class MySearchBehaviour(TickerBehaviour):
    """This class provides a simple search behaviour."""

    def __init__(self, **kwargs):
        """Initialize the search behaviour."""
        super().__init__(**kwargs)
        self.sent_search_count = 0

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        self.context.logger.info(
            "[{}]: setting up MySearchBehaviour".format(self.context.agent_name)
        )

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        self.sent_search_count += 1
        search_constraints = [Constraint("country", ConstraintType("==", "UK"))]
        search_query_w_empty_model = Query(search_constraints, model=None)
        search_request = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=(str(self.sent_search_count), ""),
            query=search_query_w_empty_model,
        )
        self.context.logger.info(
            "[{}]: sending search request to OEF search node, search_count={}".format(
                self.context.agent_name, self.sent_search_count
            )
        )
        self.context.outbox.put_message(
            to=self.context.search_service_address,
            sender=self.context.agent_address,
            protocol_id=OefSearchMessage.protocol_id,
            message=OefSearchSerializer().encode(search_request),
        )

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self.context.logger.info(
            "[{}]: tearing down MySearchBehaviour".format(self.context.agent_name)
        )
```

Searches are proactive and, as such, well placed in a `Behaviour`. Specifically, we subclass the `TickerBehaviour` as it allows us to repeatedly search at a defined tick interval.

We place this code in `my_aea/skills/my_search/behaviours.py`.

## Step 3: Develop a Handler

So far, we have tasked the AEA with sending search requests to the [OEF search node](../oef-ledger). However, we have no way of handling the responses sent to the AEA by the [OEF search node](../oef-ledger) at the moment. The AEA would simply respond to the [OEF search node](../oef-ledger) via the default `error` skill which sends all unrecognised envelopes back to the sender.

Let us now implement a handler to deal with the incoming search responses.

``` python
from aea.skills.base import Handler

from packages.fetchai.protocols.oef_search.message import OefSearchMessage


class MySearchHandler(Handler):
    """This class provides a simple search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.received_search_count = 0

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info("[{}]: setting up MySearchHandler".format(self.context.agent_name))

    def handle(self, message: OefSearchMessage) -> None:
        """
        Handle the message.

        :param message: the message.
        :return: None
        """
        msg_type = OefSearchMessage.Performative(message.performative)

        if msg_type is OefSearchMessage.Performative.SEARCH_RESULT:
            self.received_search_count += 1
            nb_agents_found = len(message.get("agents"))
            self.context.logger.info(
                "[{}]: found number of agents={}, received search count={}".format(
                    self.context.agent_name, nb_agents_found, self.received_search_count
                )
            )
        self.context.logger.info(
            "[{}]: number of search requests sent={} vs. number of search responses received={}".format(
                self.context.agent_name,
                self.context.behaviours.my_search_behaviour.sent_search_count,
                self.received_search_count,
            )
        )

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        self.context.logger.info(
            "[{}]: tearing down MySearchHandler".format(self.context.agent_name)
        )
```

We create a handler which is registered for the `oef_search` protocol. Whenever it receives a search result, we log the number of agents returned in the search - the agents matching the search query - and update the counter of received searches.

We also implement a trivial check on the difference between the amount of search requests sent and responses received.

Note, how the handler simply reacts to incoming events (i.e. messages). It could initiate further actions, however, they are still reactions to the upstream search event.

Also note, how we have access to other objects in the skill via `self.context`.

We place this code in `my_aea/skills/my_search/handlers.py`.

## Step 4: Remove unused Task and Model

We have implemented a behaviour and a handler. We could also implement a `task` and a `model`, but instead we delete these files in this case, to keep it simple.

We remove the files `my_aea/skills/my_search/tasks.py` and `my_aea/skills/my_search/my_model.py`.

## Step 5: Create the config file

Based on our skill components above, we create the following config file.

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

Ensure, you replace the author field with your author name! (Run `aea init` to set or check the author name.)

Importantly, the keys `my_search_behaviour` and `my_search_handler` are used in the above handler to access these skill components at runtime via the context. We also set the `tick_interval` of the `TickerBehaviour` to `5` seconds.

We place this code in `my_aea/skills/my_search/skill.yaml`.

## Step 6: Add the oef protocol and connection

Our AEA does not have the oef protocol yet so let's add it.
``` bash
aea add protocol fetchai/oef_search:0.1.0
```

This adds the protocol to our AEA and makes it available on the path `packages.fetchai.protocols...`.

We also need to add the oef connection and install its dependencies:
``` bash
aea add connection fetchai/oef:0.1.0
aea install
```

## Step 7: Run a service provider AEA

We first start a local [OEF search and communication node](../oef-ledger) in a separate terminal window.

``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

In order to be able to find another AEA when searching, from a different terminal window, we fetch and run another finished AEA:
```
aea fetch fetchai/simple_service_registration:0.1.0 && cd simple_service_registration
aea run
```

This AEA will simply register a location service on the [OEF search node](../oef-ledger) so we can search for it.

<details><summary>Click here to see full code</summary>
<p>

We use a ticker behaviour to update the service registration at regular intervals. The following code is placed in `behaviours.py`.

``` python
from typing import Optional, cast

from aea.helpers.search.models import Description
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.oef_search.serialization import OefSearchSerializer
from packages.fetchai.skills.simple_service_registration.strategy import Strategy

DEFAULT_SERVICES_INTERVAL = 30.0


class ServiceRegistrationBehaviour(TickerBehaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        services_interval = kwargs.pop(
            "services_interval", DEFAULT_SERVICES_INTERVAL
        )  # type: int
        super().__init__(tick_interval=services_interval, **kwargs)
        self._registered_service_description = None  # type: Optional[Description]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        self._register_service()

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        self._unregister_service()
        self._register_service()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self._unregister_service()

    def _register_service(self) -> None:
        """
        Register to the OEF search node's service directory.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        desc = strategy.get_service_description()
        self._registered_service_description = desc
        oef_msg_id = strategy.get_next_oef_msg_id()
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=(str(oef_msg_id), ""),
            service_description=desc,
        )
        self.context.outbox.put_message(
            to=self.context.search_service_address,
            sender=self.context.agent_address,
            protocol_id=OefSearchMessage.protocol_id,
            message=OefSearchSerializer().encode(msg),
        )
        self.context.logger.info(
            "[{}]: updating services on OEF search node's service directory.".format(self.context.agent_name)
        )

    def _unregister_service(self) -> None:
        """
        Unregister service from OEF search node's service directory.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        oef_msg_id = strategy.get_next_oef_msg_id()
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=(str(oef_msg_id), ""),
            service_description=self._registered_service_description,
        )
        self.context.outbox.put_message(
            to=self.context.search_service_address,
            sender=self.context.agent_address,
            protocol_id=OefSearchMessage.protocol_id,
            message=OefSearchSerializer().encode(msg),
        )
        self.context.logger.info(
            "[{}]: unregistering services from search OEF node's service directory.".format(self.context.agent_name)
        )
        self._registered_service_description = None
```

We create a generic data model to register the service. The following code is placed in `data_model.py`.

``` python
from typing import Any, Dict, List

from aea.helpers.search.models import Attribute, DataModel

SUPPORTED_TYPES = {"str": str, "int": int, "float": float, "bool": bool}


class GenericDataModel(DataModel):
    """Data model for the service."""

    def __init__(self, datamodel_name: str, data_model_attributes: Dict[str, Any]):
        """Initialise the data model."""
        self.attributes = []  # type: List[Attribute]
        for values in data_model_attributes.values():
            assert (
                values["type"] in SUPPORTED_TYPES.keys()
            ), "Type is not supported. Use str, int, float or bool"
            assert isinstance(
                values["name"], (SUPPORTED_TYPES[values["type"]],)
            ), "The datamodel values are of wrong type!"
            assert isinstance(
                values["is_required"], bool
            ), "Wrong type!! is_required must be bool"
            self.attributes.append(
                Attribute(
                    name=values["name"],  # type: ignore
                    type=SUPPORTED_TYPES[values["type"]],
                    is_required=values["is_required"],
                )
            )

        super().__init__(datamodel_name, self.attributes)
```

We create a `model` type strategy class and place it in `strategy.py`.

``` python

from typing import Any, Dict, Optional

from aea.helpers.search.models import Description
from aea.skills.base import Model

from packages.fetchai.skills.simple_service_registration.data_model import (
    GenericDataModel,
)

DEFAULT_DATA_MODEL_NAME = "location"
DEFAULT_DATA_MODEL = {
    "attribute_one": {"name": "country", "type": "str", "is_required": "True"},
    "attribute_two": {"name": "city", "type": "str", "is_required": "True"},
}  # type: Optional[Dict[str, Any]]
DEFAULT_SERVICE_DATA = {"country": "UK", "city": "Cambridge"}


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        super().__init__(**kwargs)
        self._oef_msg_id = 0
        self._data_model_name = kwargs.pop("data_model_name", DEFAULT_DATA_MODEL_NAME)
        self._data_model = kwargs.pop("data_model", DEFAULT_DATA_MODEL)
        self._service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)

    def get_next_oef_msg_id(self) -> int:
        """
        Get the next oef msg id.

        :return: the next oef msg id
        """
        self._oef_msg_id += 1
        return self._oef_msg_id

    def get_service_description(self) -> Description:
        """
        Get the service description.

        :return: a description of the offered services
        """
        desc = Description(
            self._service_data,
            data_model=GenericDataModel(self._data_model_name, self._data_model),
        )
        return desc
```

The associated `skill.yaml` is:

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
</p>
</details>

## Step 8: Run the Search AEA

We can then launch our AEA.

```bash
aea run --connections fetchai/oef:0.1.0
```

We can see that the AEA sends search requests to the [OEF search node](../oef-ledger) and receives search responses from the [OEF search node](../oef-ledger). Since our AEA is only searching on the [OEF search node](../oef-ledger) - and not registered on the [OEF search node](../oef-ledger) - the search response returns a single agent (the service provider).

We stop the AEA with `CTRL + C`.

## Now it's your turn

We hope this step by step introduction has helped you develop your own skill. We are excited to see what you will build.

<br />
