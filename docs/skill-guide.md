<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>Before developing your first skill, please read the <a href="../skill/">skill guide</a>.</p>
</div>

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Step 1: Setup

We will first create an AEA and add a scaffold skill, which we call `my_search`.

```bash
aea create my_aea && cd my_aea
aea scaffold skill my_search
```

In the following steps, we replace each one of the scaffolded `Behaviour`, `Handler` and `Task` in `my_aea/skills/my_search` with our implementation. We will build a simple skill which lets the AEA send a search query to the [OEF](../oef-ledger) and process the resulting response.

## Step 2: Develop a Behaviour

A `Behaviour` class contains the business logic specific to initial actions initiated by the AEA rather than reactions to other events.

In this example, we implement a simple search behaviour. Each time, `act()` gets called by the main agent loop, we will send a search request to the OEF.

```python
import logging

from aea.helpers.search.models import Constraint, ConstraintType, Query
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer

logger = logging.getLogger("aea.my_search_skill")


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
        logger.info(
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
        search_request = OEFMessage(
            type=OEFMessage.Type.SEARCH_SERVICES,
            id=self.sent_search_count,
            query=search_query_w_empty_model,
        )
        logger.info(
            "[{}]: sending search request to OEF, search_count={}".format(
                self.context.agent_name, self.sent_search_count
            )
        )
        self.context.outbox.put_message(
            to=DEFAULT_OEF,
            sender=self.context.agent_address,
            protocol_id=OEFMessage.protocol_id,
            message=OEFSerializer().encode(search_request),
        )

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        logger.info(
            "[{}]: tearing down MySearchBehaviour".format(self.context.agent_name)
        )
```

Searches are proactive and, as such, well placed in a `Behaviour`. Specifically, we subclass the `TickerBehaviour` as it allows us to repeatedly search at a defined tick interval.

We place this code in `my_aea/skills/my_search/behaviours.py`.

## Step 3: Develop a Handler

So far, we have tasked the AEA with sending search requests to the OEF. However, we have no way of handling the responses sent to the AEA by the OEF at the moment. The AEA would simply respond to the OEF via the default `error` skill which sends all unrecognised envelopes back to the sender.

Let us now implement a handler to deal with the incoming search responses.

```python
import logging

from aea.skills.base import Handler

from packages.fetchai.protocols.oef.message import OEFMessage

logger = logging.getLogger("aea.my_search_skill")


class MySearchHandler(Handler):
    """This class provides a simple search handler."""

    SUPPORTED_PROTOCOL = OEFMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.received_search_count = 0

    def setup(self) -> None:
        """Set up the handler."""
        logger.info("[{}]: setting up MySearchHandler".format(self.context.agent_name))

    def handle(self, message: OEFMessage) -> None:
        """
        Handle the message.

        :param message: the message.
        :return: None
        """
        msg_type = OEFMessage.Type(message.get("type"))

        if msg_type is OEFMessage.Type.SEARCH_RESULT:
            self.received_search_count += 1
            nb_agents_found = len(message.get("agents"))
            logger.info(
                "[{}]: found number of agents={}, received search count={}".format(
                    self.context.agent_name, nb_agents_found, self.received_search_count
                )
            )

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        logger.info(
            "[{}]: tearing down MySearchHandler".format(self.context.agent_name)
        )
```

We create a handler which is registered for the `oef` protocol. Whenever it receives a search result, we log the number of agents returned in the search - the agents matching the search query - and update the counter of received searches.

Note, how the handler simply reacts to incoming events (i.e. messages). It could initiate further actions, however, they are still reactions to the upstream search event.

We place this code in `my_aea/skills/my_search/handlers.py`.

## Step 4: Develop a Task

We have implemented a behaviour and a handler. We conclude by implementing a task. Here we can implement background logic. We will implement a trivial check on the difference between the amount of search requests sent and responses received.

```python
import logging
import time

from aea.skills.tasks import Task

logger = logging.getLogger("aea.my_search_skill")


class MySearchTask(Task):
    """This class scaffolds a task."""

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        logger.info("[{}]: setting up MySearchTask".format(self.context.agent_name))

    def execute(self) -> None:
        """
        Implement the task execution.

        :return: None
        """
        time.sleep(1)  # to slow down the AEA
        logger.info(
            "[{}]: number of search requests sent={} vs. number of search responses received={}".format(
                self.context.agent_name,
                self.context.behaviours.my_search_behaviour.sent_search_count,
                self.context.handlers.my_search_handler.received_search_count,
            )
        )

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        logger.info("[{}]: tearing down MySearchTask".format(self.context.agent_name))
```

Note, how we have access to other objects in the skill via `self.context`.

We place this code in `my_aea/skills/my_search/tasks.py`.

## Step 5: Create the config file

Based on our skill components above, we create the following config file.

```yaml
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
  my_search_task:
    class_name: MySearchTask
    args: {}
models: {}
protocols: ['fetchai/oef:0.1.0']
dependencies: {}
```

Importantly, the keys `my_search_behaviour` and `my_search_handler` are used in the above task to access these skill components at runtime. We also set the `tick_interval` of the `TickerBehaviour` to `5` seconds.

We place this code in `my_aea/skills/my_search/skill.yaml`.

## Step 6: Add the oef protocol and connection

Our AEA does not have the oef protocol yet so let's add it.
```bash
aea add protocol fetchai/oef:0.1.0
```

This adds the protocol to our AEA and makes it available on the path `packages.fetchai.protocols...`.

We also need to add the oef connection:
```bash
aea add connection fetchai/oef:0.1.0
```

## Step 7: Run the AEA

We first start an oef node (see the <a href="../connection/" target=_blank>connection section</a> for more details) in a separate terminal window.

```bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

We can then launch our AEA.

```bash
aea run --connections fetchai/oef:0.1.0
```

We can see that the AEA sends search requests to the OEF and receives search responses from the OEF. Since our AEA is only searching on the OEF - and not registered on the OEF - the search response returns an empty list of agents.

We stop the AEA with `CTRL + C`.

## Now it's your turn

We hope this step by step introduction has helped you develop your own skill. We are excited to see what you will build.

<br />
