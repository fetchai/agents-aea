This guide will take you through the development of your first skill. It will teach you, how to connect the AEA to the digital world, register the AEA and search for other AEAs.

Although one can imagine scenarios where a single AEA pursues its goals in isolation without interacting with other AEAs, there is no doubt that by working together, AEAs can achieve much more. To do so, an AEA must be seen and found by other AEAs so that they can trade and do other useful things. Fetch.ai’s search-and-discovery mechanism, the <a href="../simple-oef">simple OEF</a> (or SOEF, for short) lets your agents register, be discovered, and find other agents. You can then negotiate using the AEA framework’s <a href="../acn">peer-to-peer network (ACN)</a> and trade. This guide covers getting your AEA connected to the SOEF, and describing your AEA to make itself visible.

Registering your AEA with the SOEF involves setting a name, a genus (a high-level description of what the agent represents, e.g. `vehicle`, `building` or `service`), a classification (for example `infrastructure.railway.train`) and other descriptors to further fine-tune the kind of service your AEA offers (for example, the agent's position, whether it buys or sells, and other descriptive items).

The more you describe your AEA, the easier it is for others to find it using specific filters.

## Dependencies (Required)

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.



## Step 1: Setup

We will first create an AEA and add a scaffold skill, which we call `my_search`.

``` bash
aea create my_aea && cd my_aea
aea scaffold skill my_search
```

In the following steps, we replace the scaffolded `Behaviour` and `Handler` in `my_aea/skills/my_search` with our implementation. We will build a simple skill which lets the AEA send a search query to the <a href="../simple-oef">SOEF search node</a> and process the resulting response.

## Step 2: Develop a Behaviour

A <a href="../api/skills/base#behaviour-objects">`Behaviour`</a> class contains the business logic specific to actions initiated by the AEA rather than reactions to other events.

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

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p> Note that the import paths to agent packages, for example <code>packages.fetchai.skills.my_search.dialogues</code> above, are not actual paths. Package files always reside in your AEA's folder, either under a specific package directory (e.g. connection, protocol, skill) if the package is custom built, or under <code>vendor</code> if it is pulled from the registry. These paths are virtual and created automatically when an AEA is run. See <a href="../package-imports"> this page </a> for more details. </p>
</div>

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

We have implemented a behaviour and a handler. We now implement a <a href="../api/skills/base#model-objects">`Model`</a>, in particular we implement the <a href="../api/protocols/dialogue/base#dialogue-objects">`Dialogue`</a> and <a href="../api/protocols/dialogue/base#dialogues-objects">`Dialogues`</a> classes. These ensure that the message flow satisfies the `fetchai/oef_search:1.0.0` protocol and keep track of the individual messages being sent and received.

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
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )
```

We add this code in the file `my_aea/skills/my_search/my_model.py`, replacing its original content. We then rename `my_aea/skills/my_search/my_model.py` to `my_aea/skills/my_search/dialogues.py`.

## Step 5: Create the configuration file

Based on our skill components above, we create the following configuration file.

``` yaml
name: my_search
author: fetchai
version: 0.1.0
type: skill
description: A simple search skill utilising the SOEF search node.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
fingerprint: {}
fingerprint_ignore_patterns: []
connections: []
contracts: []
protocols:
- fetchai/oef_search:1.0.0
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
dependencies:
  aea-ledger-fetchai:
    version: <2.0.0,>=1.0.0
is_abstract: false
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

To run an AEA with new or modified code, you need to update the fingerprint of the new/modified components. In this case, we need to fingerprint our skill:
``` bash
aea fingerprint skill fetchai/my_search:0.1.0
```
Ensure, you use the correct author name to reference your skill (here we use `fetchai` as the author.)

## Step 7: Add the OEF protocol and connection

Our AEA does not have the OEF protocol yet so let's add it.
``` bash
aea add protocol fetchai/oef_search:1.0.0
```

This adds the protocol to our AEA and makes it available on the path `packages.fetchai.protocols...`.

At this point we need to add the SOEF and P2P connections to allow the AEA to communicate with the SOEF node and other AEAs, install the AEA's dependencies, and configure the AEA:
``` bash
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/p2p_libp2p:0.25.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
```

The last command will ensure that search requests are processed by the correct connection.

## Step 8: Run a service provider AEA

In order for this AEA to find another AEA when searching, the second AEA (let's call it the service provider AEA) must exist and have been registered with the SOEF. 

From a different terminal window, we fetch a finished service provider AEA and install its Python dependencies:
``` bash
aea fetch fetchai/simple_service_registration:0.31.0 && cd simple_service_registration && aea install && aea build
```

This AEA will simply register a location service on the <a href="../simple-oef">SOEF search node</a> so we can search for it.

We first create the private key for the service provider AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `StargateWorld` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Next, create a private key used to secure the AEA's communications:
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

Finally, certify the key for use by the connections that request that:
``` bash
aea issue-certificates
```

Then we run the AEA:
``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr: ['SOME_ADDRESS']` take note of the address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.25.0 -u public_uri` to retrieve the address.) This is the entry peer address for the local <a href="../acn">agent communication network</a> created by the `simple_service_registration` (service provider) AEA.

<details><summary>Click here to see full code and guide for this AEA</summary>
<p>

We use a <a href="../api/skills/behaviours#tickerbehaviour-objects"><code>TickerBehaviour</code></a> to update the service registration at regular intervals. The following code is placed in <code>behaviours.py</code>.

``` python
from typing import Any, Optional, cast

from aea.helpers.search.models import Description
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_service_registration.dialogues import (
    OefSearchDialogues,
)
from packages.fetchai.skills.simple_service_registration.strategy import Strategy


DEFAULT_MAX_SOEF_REGISTRATION_RETRIES = 5
DEFAULT_SERVICES_INTERVAL = 30.0


class ServiceRegistrationBehaviour(TickerBehaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialise the behaviour."""
        services_interval = kwargs.pop(
            "services_interval", DEFAULT_SERVICES_INTERVAL
        )  # type: int
        self._max_soef_registration_retries = kwargs.pop(
            "max_soef_registration_retries", DEFAULT_MAX_SOEF_REGISTRATION_RETRIES
        )  # type: int
        super().__init__(tick_interval=services_interval, **kwargs)

        self.failed_registration_msg = None  # type: Optional[OefSearchMessage]
        self._nb_retries = 0

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        self._register_agent()

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        self._retry_failed_registration()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self._unregister_service()
        self._unregister_agent()

    def _retry_failed_registration(self) -> None:
        """
        Retry a failed registration.

        :return: None
        """
        if self.failed_registration_msg is not None:
            self._nb_retries += 1
            if self._nb_retries > self._max_soef_registration_retries:
                self.context.is_active = False
                return

            oef_search_dialogues = cast(
                OefSearchDialogues, self.context.oef_search_dialogues
            )
            oef_search_msg, _ = oef_search_dialogues.create(
                counterparty=self.failed_registration_msg.to,
                performative=self.failed_registration_msg.performative,
                service_description=self.failed_registration_msg.service_description,
            )
            self.context.outbox.put_message(message=oef_search_msg)
            self.context.logger.info(
                f"Retrying registration on SOEF. Retry {self._nb_retries} out of {self._max_soef_registration_retries}."
            )

            self.failed_registration_msg = None

    def _register(self, description: Description, logger_msg: str) -> None:
        """
        Register something on the SOEF.

        :param description: the description of what is being registered
        :param logger_msg: the logger message to print after the registration

        :return: None
        """
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info(logger_msg)

    def _register_agent(self) -> None:
        """
        Register the agent's location.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_location_description()
        self._register(description, "registering agent on SOEF.")

    def register_service(self) -> None:
        """
        Register the agent's service.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_register_service_description()
        self._register(description, "registering agent's service on the SOEF.")

    def register_genus(self) -> None:
        """
        Register the agent's personality genus.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_register_personality_description()
        self._register(
            description, "registering agent's personality genus on the SOEF."
        )

    def register_classification(self) -> None:
        """
        Register the agent's personality classification.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_register_classification_description()
        self._register(
            description, "registering agent's personality classification on the SOEF."
        )

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
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
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
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("unregistering agent from SOEF.")
```

We create a <a href="../api/skills/base#model-objects"><code>Model</code></a> type strategy class and place it in <code>strategy.py</code>. We use a generic data model to register the service. As part of the registration we register a location and a key pair describing our service.

``` python
from typing import Any

from aea.exceptions import enforce
from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
)
from aea.helpers.search.models import Description, Location
from aea.skills.base import Model


DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SERVICE_DATA = {"key": "seller_service", "value": "generic_service"}
DEFAULT_PERSONALITY_DATA = {"piece": "genus", "value": "data"}
DEFAULT_CLASSIFICATION = {"piece": "classification", "value": "seller"}


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = {
            "location": Location(
                latitude=location["latitude"], longitude=location["longitude"]
            )
        }
        self._set_personality_data = kwargs.pop(
            "personality_data", DEFAULT_PERSONALITY_DATA
        )
        enforce(
            len(self._set_personality_data) == 2
            and "piece" in self._set_personality_data
            and "value" in self._set_personality_data,
            "personality_data must contain keys `key` and `value`",
        )
        self._set_classification = kwargs.pop("classification", DEFAULT_CLASSIFICATION)
        enforce(
            len(self._set_classification) == 2
            and "piece" in self._set_classification
            and "value" in self._set_classification,
            "classification must contain keys `key` and `value`",
        )
        self._set_service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        enforce(
            len(self._set_service_data) == 2
            and "key" in self._set_service_data
            and "value" in self._set_service_data,
            "service_data must contain keys `key` and `value`",
        )
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

    def get_register_personality_description(self) -> Description:
        """
        Get the register personality description.

        :return: a description of the personality
        """
        description = Description(
            self._set_personality_data, data_model=AGENT_PERSONALITY_MODEL,
        )
        return description

    def get_register_classification_description(self) -> Description:
        """
        Get the register classification description.

        :return: a description of the classification
        """
        description = Description(
            self._set_classification, data_model=AGENT_PERSONALITY_MODEL,
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

We create a <a href="../api/skills/base#model-objects"><code>Model</code></a> type dialogue class and place it in <code>dialogues.py</code>. These classes ensure that the message flow satisfies the <code>fetchai/oef_search:1.0.0</code> protocol and keep track of the individual messages being sent and received.

``` python
from typing import Any

from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
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

    def __init__(self, **kwargs: Any) -> None:
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
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )

```

Finally, we have a handler, placed in <code>handlers.py</code>. The handler deals with handling any error messages which might occur during service registration:

``` python
from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_service_registration.behaviours import (
    ServiceRegistrationBehaviour,
)
from packages.fetchai.skills.simple_service_registration.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
)


class OefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Call to setup the handler."""

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
        if oef_search_msg.performative == OefSearchMessage.Performative.SUCCESS:
            self._handle_success(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative == OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """

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

    def _handle_success(
        self,
        oef_search_success_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_success_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "received oef_search success message={} in dialogue={}.".format(
                oef_search_success_msg, oef_search_dialogue
            )
        )
        target_message = cast(
            OefSearchMessage,
            oef_search_dialogue.get_message_by_id(oef_search_success_msg.target),
        )
        if (
            target_message.performative
            == OefSearchMessage.Performative.REGISTER_SERVICE
        ):
            description = target_message.service_description
            data_model_name = description.data_model.name
            registration_behaviour = cast(
                ServiceRegistrationBehaviour, self.context.behaviours.service,
            )
            if "location_agent" in data_model_name:
                registration_behaviour.register_service()
            elif "set_service_key" in data_model_name:
                registration_behaviour.register_genus()
            elif (
                "personality_agent" in data_model_name
                and description.values["piece"] == "genus"
            ):
                registration_behaviour.register_classification()
            elif (
                "personality_agent" in data_model_name
                and description.values["piece"] == "classification"
            ):
                self.context.logger.info(
                    "the agent, with its genus and classification, and its service are successfully registered on the SOEF."
                )
            else:
                self.context.logger.warning(
                    f"received soef SUCCESS message as a reply to the following unexpected message: {target_message}"
                )

    def _handle_error(
        self,
        oef_search_error_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_error_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_error_msg, oef_search_dialogue
            )
        )
        target_message = cast(
            OefSearchMessage,
            oef_search_dialogue.get_message_by_id(oef_search_error_msg.target),
        )
        if (
            target_message.performative
            == OefSearchMessage.Performative.REGISTER_SERVICE
        ):
            registration_behaviour = cast(
                ServiceRegistrationBehaviour, self.context.behaviours.service,
            )
            registration_behaviour.failed_registration_msg = target_message

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

The associated <code>skill.yaml</code> is:

``` yaml
name: simple_service_registration
author: fetchai
version: 0.20.0
type: skill
description: The simple service registration skills is a skill to register a service.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
fingerprint:
  README.md: QmUgCcR7sDBQeeCBRKwDT7tPBTi3t4zSibyEqR3xdQUKmh
  __init__.py: QmZd48HmYDr7FMxNaVeGfWRvVtieEdEV78hd7h7roTceP2
  behaviours.py: QmQHf6QL5aBtLJ34D2tdcbjJLbzom9gaA3HWgRn3rWyigM
  dialogues.py: QmTT9dvFhWt6qvxjwBfMFDTrgEtgWbvgANYafyRg2BXwcR
  handlers.py: QmZqPt8toGbJgTT6NZBLxjkusrQCZ8GmUEwcmqZ1sd7DpG
  strategy.py: QmVXfQpk4cjDw576H2ELE12tEiN5brPkwvffvcTeMbsugA
fingerprint_ignore_patterns: []
connections: []
contracts: []
protocols:
- fetchai/oef_search:1.0.0
skills: []
behaviours:
  service:
    args:
      max_soef_registration_retries: 5
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
      classification:
        piece: classification
        value: seller
      location:
        latitude: 51.5194
        longitude: 0.127
      personality_data:
        piece: genus
        value: data
      service_data:
        key: seller_service
        value: generic_service
    class_name: Strategy
dependencies: {}
is_abstract: false
```
</p>
</details>

## Step 9: Run the Search AEA

First, create the private key for the search AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `StargateWorld` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Next, create a private key used to secure the AEA's communications:
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

Finally, certify the key for use by the connections that request that:
``` bash
aea issue-certificates
```

Then, in the search AEA, run this command (replace `SOME_ADDRESS` with the correct value as described above):
``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAm1uJpFsqSgHStJdtTBPpDme1fo8uFEvvY182D2y89jQuj"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}'
```
This allows the search AEA to connect to the same local agent communication network as the service registration AEA.

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

<a href="../generic-skills-step-by-step"> This guide </a> goes through a more elaborate scenario than the one on this page, where after finding each other, the two AEAs negotiate and trade via a ledger. 

<br />