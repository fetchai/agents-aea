This guide will take you through the development of a simple skill.

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Step 1: Setup

We will first create an AEA and add a scaffold skill, which we call `my_search`.

``` bash
aea create my_aea && cd my_aea
aea scaffold skill my_search
```

In the following steps, we replace the scaffolded `Behaviour` and `Handler` in `my_aea/skills/my_search` with our implementation. We will build a simple skill which lets the AEA send a search query to the <a href="../simple-oef">SOEF search node</a> and process the resulting response.

## Step 2: Develop a Behaviour

A <a href="../api/skills/base#behaviour-objects">`Behaviour`</a> class contains the business logic specific to initial actions initiated by the AEA rather than reactions to other events.

In this example, we implement a simple search behaviour. Each time, `act()` gets called by the main agent loop, we will send a search request to the <a href="../simple-oef">SOEF search node</a> via the <a href="../oef-ledger">P2P communication network</a>.

``` python
from typing import cast

from aea.helpers.search.models import Constraint, ConstraintType, Location, Query
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.my_search.dialogues import OefSearchDialogues

DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SEARCH_QUERY = {
    "search_key": "seller_service",
    "search_value": "generic_service",
    "constraint_type": "==",
}
DEFAULT_SEARCH_RADIUS = 5.0


class MySearchBehaviour(TickerBehaviour):
    """This class provides a simple search behaviour."""

    def __init__(self, **kwargs):
        """Initialize the search behaviour."""

        search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        location = kwargs.pop("location", DEFAULT_LOCATION)
        agent_location = Location(latitude=location["latitude"], longitude=location["longitude"])
        radius = kwargs.pop("search_radius", DEFAULT_SEARCH_RADIUS)

        close_to_my_service = Constraint(
            "location", ConstraintType("distance", (agent_location, radius))
        )
        service_key_filter = Constraint(
            search_query["search_key"],
            ConstraintType(
                search_query["constraint_type"], search_query["search_value"],
            ),
        )
        self.query = Query([close_to_my_service, service_key_filter])
        super().__init__(**kwargs)
        self.sent_search_count = 0

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        self.context.logger.info(
            "setting up MySearchBehaviour"
        )

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        self.sent_search_count += 1
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        self.context.logger.info(
            "sending search request to OEF search node, search_count={}".format(
                self.sent_search_count
            )
        )
        search_request, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=self.query,
        )
        self.context.outbox.put_message(message=search_request)

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self.context.logger.info(
            "tearing down MySearchBehaviour"
        )
```

Searches are proactive and, as such, well placed in a <a href="../api/skills/base#behaviour-objects">`Behaviour`</a>. Specifically, we subclass the <a href="../api/skills/behaviours#tickerbehaviour-objects">`TickerBehaviour`</a> as it allows us to repeatedly search at a defined tick interval.

We place this code in `my_aea/skills/my_search/behaviours.py`. Ensure you replace the `fetchai` author in this line `from packages.fetchai.skills.my_search.dialogues import OefSearchDialogues` with your author handle (run `aea init` to set or check the author name).

## Step 3: Develop a Handler

So far, we have tasked the AEA with sending search requests to the <a href="../simple-oef">SOEF search node</a>. However, we have no way of handling the responses sent to the AEA by the <a href="../simple-oef">SOEF search node</a> at the moment. The AEA would simply respond to the <a href="../simple-oef">SOEF search node</a> via the default `error` skill which sends all unrecognised envelopes back to the sender.

Let us now implement a <a href="../api/skills/base#handler-objects">`Handler`</a> to deal with the incoming search responses.

``` python
from typing import Optional, cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.my_search.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
)


class MySearchHandler(Handler):
    """This class provides a simple search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.received_search_count = 0

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info(
            "setting up MySearchHandler"
        )

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        oef_search_msg = cast(OefSearchMessage, message)

        # recover dialogue
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_dialogue = cast(
            Optional[OefSearchDialogue], oef_search_dialogues.update(oef_search_msg)
        )
        if oef_search_dialogue is None:
            self._handle_unidentified_dialogue(oef_search_msg)
            return

        # handle message
        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            self._handle_search(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _handle_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_msg, oef_search_dialogue
            )
        )

    def _handle_search(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :return: None
        """
        self.received_search_count += 1
        nb_agents_found = len(oef_search_msg.agents)
        self.context.logger.info(
            "found number of agents={}, received search count={}".format(
                nb_agents_found, self.received_search_count
            )
        )
        self.context.logger.info(
            "number of search requests sent={} vs. number of search responses received={}".format(
                self.context.behaviours.my_search_behaviour.sent_search_count,
                self.received_search_count,
            )
        )

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        self.context.logger.info(
            "tearing down MySearchHandler"
        )
```

We create a handler which is registered for the `oef_search` protocol. Whenever it receives a search result, we log the number of agents returned in the search - the agents matching the search query - and update the counter of received searches.

We also implement a trivial check on the difference between the amount of search requests sent and responses received.

Note, how the handler simply reacts to incoming events (i.e. messages). It could initiate further actions, however, they are still reactions to the upstream search event.

Also note, how we have access to other objects in the skill via `self.context`, the <a href="../api/skills/base#skillcontext-objects">`SkillContext`</a>.

We place this code in `my_aea/skills/my_search/handlers.py`. Ensure you replace the `fetchai` author in this line `from packages.fetchai.skills.my_search.dialogues import (` with your author handle (run `aea init` to set or check the author name).

## Step 4: Add dialogues model

We have implemented a behaviour and a handler. We now implement a <a href="../api/skills/base#model-objects">`Model`</a>, in particular we implement the <a href="../api/helpers/dialogue/base#dialogue-objects">`Dialogue`</a> and <a href="../api/helpers/dialogue/base#dialogues-objects">`Dialogues`</a> classes.

``` python
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.skills.base import Address, Model

from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)


OefSearchDialogue = BaseOefSearchDialogue


class OefSearchDialogues(Model, BaseOefSearchDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseOefSearchDialogue.Role.AGENT

        BaseOefSearchDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
        )
```

We add this code in the file `my_aea/skills/my_search/my_model.py`, replacing its original content. We then renamce `my_aea/skills/my_search/my_model.py` to `my_aea/skills/my_search/dialogues.py`.

## Step 5: Create the config file

Based on our skill components above, we create the following config file.

``` yaml
name: my_search
author: fetchai
version: 0.1.0
type: skill
description: A simple search skill utilising the SOEF search node.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
fingerprint: {}
fingerprint_ignore_patterns: []
contracts: []
protocols:
- fetchai/oef_search:0.9.0
skills: []
behaviours:
  my_search_behaviour:
    args:
      location:
        latitude: 51.5194
        longitude: 0.127
      search_query:
        constraint_type: ==
        search_key: seller_service
        search_value: generic_service
      search_radius: 5.0
      tick_interval: 5
    class_name: MySearchBehaviour
handlers:
  my_search_handler:
    args: {}
    class_name: MySearchHandler
models:
  oef_search_dialogues:
    args: {}
    class_name: OefSearchDialogues
dependencies: {}
```

Ensure, you replace the author field with your author name! (Run `aea init` to set or check the author name.)

Importantly, the keys `my_search_behaviour` and `my_search_handler` are used in the above handler to access these skill components at runtime via the context. We also set the `tick_interval` of the `TickerBehaviour` to `5` seconds.

We place this code in `my_aea/skills/my_search/skill.yaml`.

Similarly, we replace `my_aea/skills/my_search/__init__.py` as follows:

``` python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains the implementation of the error skill."""

from aea.configurations.base import PublicId


PUBLIC_ID = PublicId.from_str("fetchai/my_search:0.1.0")

```
Again, ensure the author field matches your own.

## Step 6: Update fingerprint

We need to update the fingerprint of our skill next:
``` bash
aea fingerprint skill fetchai/my_search:0.1.0
```
Ensure, you use the correct author name to reference your skill (here we use `fetchai` as the author.)

## Step 7: Add the oef protocol and connection

Our AEA does not have the oef protocol yet so let's add it.
``` bash
aea add protocol fetchai/oef_search:0.9.0
```

This adds the protocol to our AEA and makes it available on the path `packages.fetchai.protocols...`.

We also need to add the soef and p2p connections and install the AEA's dependencies:
``` bash
aea add connection fetchai/soef:0.11.0
aea add connection fetchai/p2p_libp2p:0.12.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.12.0
```

Finally, in the `aea-config.yaml` add the following lines:
``` yaml
default_routing:
  fetchai/oef_search:0.9.0: fetchai/soef:0.11.0
```

This will ensure that search requests are processed by the correct connection.

## Step 8: Run a service provider AEA

In order to be able to find another AEA when searching, from a different terminal window, we fetch another finished AEA and install its Python dependencies:
``` bash
aea fetch fetchai/simple_service_registration:0.15.0 && cd simple_service_registration && aea install
```

This AEA will simply register a location service on the <a href="../simple-oef">SOEF search node</a> so we can search for it.

We first create the private key for the service provider AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `AgentLand` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
```

Then we run the aea:
``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr: ['SOME_ADDRESS']` take note of the address.

<details><summary>Click here to see full code</summary>
<p>

We use a <a href="../api/skills/behaviours#tickerbehaviour-objects">`TickerBehaviour`</a> to update the service registration at regular intervals. The following code is placed in `behaviours.py`.

``` python
from typing import cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_service_registration.dialogues import (
    OefSearchDialogues,
)
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

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        self._register_agent()
        self._register_service()

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        pass

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self._unregister_service()
        self._unregister_agent()

    def _register_agent(self) -> None:
        """
        Register the agent's location.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_location_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=description,
        )
        oef_search_msg.counterparty = self.context.search_service_address
        oef_search_dialogues.update(oef_search_msg)
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("registering agent on SOEF.")

    def _register_service(self) -> None:
        """
        Register the agent's service.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_register_service_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=description,
        )
        oef_search_msg.counterparty = self.context.search_service_address
        oef_search_dialogues.update(oef_search_msg)
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("registering service on SOEF.")

    def _unregister_service(self) -> None:
        """
        Unregister service from the SOEF.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_unregister_service_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=description,
        )
        oef_search_msg.counterparty = self.context.search_service_address
        oef_search_dialogues.update(oef_search_msg)
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("unregistering service from SOEF.")

    def _unregister_agent(self) -> None:
        """
        Unregister agent from the SOEF.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_location_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=description,
        )
        oef_search_msg.counterparty = self.context.search_service_address
        oef_search_dialogues.update(oef_search_msg)
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("unregistering agent from SOEF.")
```

We create a <a href="../api/skills/base#model-objects">`Model`</a> type strategy class and place it in `strategy.py`. We use a generic data model to register the service.

``` python
from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
)
from aea.helpers.search.models import Description, Location
from aea.skills.base import Model

DEFAULT_LOCATION = {"longitude": 51.5194, "latitude": 0.1270}
DEFAULT_SERVICE_DATA = {"key": "seller_service", "value": "generic_service"}


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = {
            "location": Location(latitude=location["latitude"], longitude=location["longitude"])
        }
        self._set_service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        assert (
            len(self._set_service_data) == 2
            and "key" in self._set_service_data
            and "value" in self._set_service_data
        ), "service_data must contain keys `key` and `value`"
        self._remove_service_data = {"key": self._set_service_data["key"]}
        super().__init__(**kwargs)

    def get_location_description(self) -> Description:
        """
        Get the location description.

        :return: a description of the agent's location
        """
        description = Description(
            self._agent_location, data_model=AGENT_LOCATION_MODEL,
        )
        return description

    def get_register_service_description(self) -> Description:
        """
        Get the register service description.

        :return: a description of the offered services
        """
        description = Description(
            self._set_service_data, data_model=AGENT_SET_SERVICE_MODEL,
        )
        return description

    def get_unregister_service_description(self) -> Description:
        """
        Get the unregister service description.

        :return: a description of the to be removed service
        """
        description = Description(
            self._remove_service_data, data_model=AGENT_REMOVE_SERVICE_MODEL,
        )
        return description
```

We create a <a href="../api/skills/base#model-objects">`Model`</a> type dialogue class and place it in `dialogues.py`.

``` python
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.skills.base import Model

from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)


OefSearchDialogue = BaseOefSearchDialogue


class OefSearchDialogues(Model, BaseOefSearchDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseOefSearchDialogue.Role.AGENT

        BaseOefSearchDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
        )

```

Finally, we have a handler, placed in `handlers.py`:

``` python
from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_service_registration.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
)

LEDGER_API_ADDRESS = "fetchai/ledger:0.8.0"


class OefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        oef_search_msg = cast(OefSearchMessage, message)

        # recover dialogue
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_dialogue = cast(
            Optional[OefSearchDialogue], oef_search_dialogues.update(oef_search_msg)
        )
        if oef_search_dialogue is None:
            self._handle_unidentified_dialogue(oef_search_msg)
            return

        # handle message
        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _handle_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_msg, oef_search_dialogue
            )
        )

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
```

The associated `skill.yaml` is:

``` yaml
name: simple_service_registration
author: fetchai
version: 0.4.0
type: skill
description: The simple service registration skills is a skill to register a service.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
fingerprint:
  __init__.py: QmNkZAetyctaZCUf6ACxP5onGWsSxu2hjSNoFmJ3ta6Lta
  behaviours.py: QmRr1oe3zWKyPcktzKP4BiKqjCqmKjEDdLUQhn1JzNm4nD
  dialogues.py: QmayFh6ytPefJng5ENTUg46zsd6guHCZSsG3Cc2sy3xz6y
  handlers.py: QmViyyV5KvR3kkLEMpvDfqH5QtHowTbnpDxRYnKABpVvpC
  strategy.py: Qmdp6LCPZSnnyfM4EdRDTGZPqwxiJ3A1jsc3oF2Hv4m5Mv
fingerprint_ignore_patterns: []
contracts: []
protocols:
- fetchai/oef_search:0.9.0
skills: []
behaviours:
  service:
    args:
      services_interval: 30
    class_name: ServiceRegistrationBehaviour
handlers:
  oef_search:
    args: {}
    class_name: OefSearchHandler
models:
  oef_search_dialogues:
    args: {}
    class_name: OefSearchDialogues
  strategy:
    args:
      location:
        latitude: 51.5194
        longitude: 0.127
      service_data:
        key: seller_service
        value: generic_service
    class_name: Strategy
dependencies: {}
```
</p>
</details>

## Step 9: Run the Search AEA

First, create the private key for the search AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `AgentLand` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
```

Then, update the configuration of the search AEA's p2p connection (in `vendor/fetchai/connections/p2p_libp2p/connection.yaml`) replace the following:

``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```

where `SOME_ADDRESS` is replaced accordingly.

We can then launch our AEA.

``` bash
aea run
```

We can see that the AEA sends search requests to the <a href="../simple-oef">SOEF search node</a> and receives search responses from the <a href="../simple-oef">SOEF search node</a>. The search response returns one or more agents (the service provider and potentially other agents which match the query).

We stop the AEA with `CTRL + C`.

## Next steps


### Recommended

We recommend you continue with the next step in the 'Getting Started' series:

- <a href="../core-components-2">Core components (Part 2)</a>


### Relevant deep-dives

We hope this step by step introduction has helped you develop your own skill. We are excited to see what you will build.

<br />