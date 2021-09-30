In this guide we describe some of the tools the framework offers for testing skills.

## The `BaseSkillTestCase` class

The framework offers a <a href="../api/test_tools/test_skill#baseskilltestcase-objects">`BaseSkillTestCase`</a> class which you can subclass and write your test cases with. 

Let us assume you want to test the `my_behaviour` behaviour of a `CustomSkill` skill you have developed. 

You can create a `TestMyBehaviour` class which inherits `BaseSkillTestCase` as below:

``` python
import asyncio

from asyncio import Queue
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from aea.configurations.constants import DEFAULT_LEDGER
from aea.context.base import AgentContext
from aea.crypto.ledger_apis import DEFAULT_CURRENCY_DENOMINATIONS
from aea.identity.base import Identity
from aea.multiplexer import AsyncMultiplexer, OutBox, Multiplexer
from aea.skills.tasks import TaskManager
from aea.test_tools.test_skill import BaseSkillTestCase

class TestMyBehaviour(BaseSkillTestCase):
    """Test my_behaviours of the custom skill."""

    path_to_skill = Path("path_to_this_skill")
```

### Specifying Skill Path

You must then specify the path to your skill directory via `path_to_skill` to allow the skill to be loaded and tested. This must be the directory in which `skill.yaml` of your skill resides.

### Setting up Each Test

You can add a `setup()` class method to set the environment up for each of your tests. This code will be executed before every test method. If you do include this method, you must call the `setup()` method of the `BaseSkillTestCase` class via `super().setup()`.

``` python
@classmethod
def setup(cls):
    """Setup the test class."""
    super().setup()
    cls.my_behaviour = cast(
        MyBehaviour, cls._skill.skill_context.behaviours.my_behaviour
    )
```

In the above, we make the `my_behaviour` behaviour object accessible for every test.

### Skill and Skill Context

The skill object itself is exposed via a property. So you can access the skill object by `self.skill` and by extension all of its attributes. This crucially includes the complete `skill_context`. This means that for example, all of the components of the skill (e.g. behaviours, handlers, models) can be accessed via the skill context. 

In the above code snippet, `my_behavior` is accessed and exposed as a class attribute. Note accessing the skill context is slightly different in the above because it is a class method. If this was a test method, you could access the behaviour via `self.skill.skill_context.behaviours.my_behaviour`.

### Dummy Agent Context

The loaded skill is also fed a dummy `agent_context` complete with an `identity`, `outbox`, `decision_maker_queue` and so on, to allow the skill to be properly loaded and have access to everything it requires to function. The `agent_context` object fed to the skill is shown below:

``` python
_multiplexer = AsyncMultiplexer()
_multiplexer._out_queue = (asyncio.Queue())

agent_context = AgentContext(
    identity=Identity("test_agent_name", "test_agent_address", "test_agent_public_key"),
    connection_status=_multiplexer.connection_status,
    outbox=OutBox(cast(Multiplexer, cls._multiplexer)),
    decision_maker_message_queue=Queue(),
    decision_maker_handler_context=SimpleNamespace(),
    task_manager=TaskManager(),
    default_ledger_id=DEFAULT_LEDGER,
    currency_denominations={},
    default_connection=None,
    default_routing={},
    search_service_address="dummy_search_service_address",
    decision_maker_address="dummy_decision_maker_address",
    data_dir="."
)
```

### Some Useful Skill Attributes

Some of the useful objects you can access in your test class for the loaded skill are below:

* `self.skill.skill_context.agent_address`: this is the agent identity the skill uses and is set to `"test_agent_address"`.
* `self.skill.skill_context.search_service_address`: this is the address of the search service and is set to `"dummy_search_service_address"`.
* `self.skill.skill_context.skill_id`: this is the id of the skill.
* `self.skill.skill_context.decision_maker_address`: this is the address of the decision maker and is set to `"dummy_decision_maker_address"`.

### Some Useful `BaseSkillTestCase` Methods

There are a number of methods that `BaseSkillTestCase` offers to make testing skills easier. Some of these are mentioned below. For the rest, consult the API for `BaseSkillTestCase`:

* `self.get_quantity_in_outbox()`: gives you the number of messages which are in the outbox. After running a part of the skill which is expected to send messages, you can use this method to assert the correct number of messages are indeed sent.
* `self.get_message_from_outbox()`: gives you the last message in the outbox. Together with the above, you can use this method to grab the last message sent by the skill code you tested and check this is indeed the expected message.
* `self.message_has_attributes(actual_message: Message, message_type: Type[Message], **kwargs,)`: you can use this method in tandem with the above method to check that a message has the attributes you expect it to have. You have to supply it with the actual message (e.g. using `self.get_message_from_outbox()`), specify its expected type (e.g. `FipaMessage`), and any other attribute you expect the message to have (e.g. `message_id` is 1) may be provided via keyword arguments.
* `self.build_incoming_message`: this is an especially useful method to test handlers. Since handlers handle incoming messages, you can create an incoming message using this method to feed it to the handler and test its execution.

#### Checking Logger Output

You can check the output of your skill's `logger` by mocking it using `unittest.mock` before executing a part of your skill as such:

``` python
import logging
from unittest import mock

with mock.patch.object(self.my_behaviour.context.logger, "log") as mock_logger:
    self.my_behaviour.act()

mock_logger.assert_any_call(logging.INFO, "some_logger_message")
```

In the above, we mock the logger before running `my_behaviour`'s `act()` method and check that  the string `"some_logger_message"` is indeed passed to the logger.

## Next steps

You can consult the `fetchai/generic_buyer` and `fetchai/generic_seller` skills and their associated tests <a href="https://github.com/fetchai/agents-aea/tree/main/tests/test_packages/test_skills" target="_blank">here</a> to study how `BaseSkillTestCase` can help you in testing your skills.

You can also refer to the API to study the different methods `BaseSkillTestCase` makes available to make testing your skills easier. 
