<a id="aea.test_tools.test_skill"></a>

# aea.test`_`tools.test`_`skill

This module contains test case classes based on pytest for AEA skill testing.

<a id="aea.test_tools.test_skill._MetaBaseSkillTestCase"></a>

## `_`MetaBaseSkillTestCase Objects

```python
class _MetaBaseSkillTestCase(ABCMeta)
```

A metaclass that validates BaseSkillTestCase's class.

<a id="aea.test_tools.test_skill._MetaBaseSkillTestCase.__new__"></a>

#### `__`new`__`

```python
def __new__(mcs, name: str, bases: Tuple, namespace: Dict,
            **kwargs: Any) -> Type
```

Initialize the class.

<a id="aea.test_tools.test_skill.BaseSkillTestCase"></a>

## BaseSkillTestCase Objects

```python
class BaseSkillTestCase(ABC, metaclass=_MetaBaseSkillTestCase)
```

A class to test a skill.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.skill"></a>

#### skill

```python
@property
def skill() -> Skill
```

Get the skill.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.get_quantity_in_outbox"></a>

#### get`_`quantity`_`in`_`outbox

```python
def get_quantity_in_outbox() -> int
```

Get the quantity of envelopes in the outbox.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.get_message_from_outbox"></a>

#### get`_`message`_`from`_`outbox

```python
def get_message_from_outbox() -> Optional[Message]
```

Get message from outbox.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.drop_messages_from_outbox"></a>

#### drop`_`messages`_`from`_`outbox

```python
def drop_messages_from_outbox(number: int = 1) -> None
```

Dismiss the first 'number' number of message from outbox.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.get_quantity_in_decision_maker_inbox"></a>

#### get`_`quantity`_`in`_`decision`_`maker`_`inbox

```python
def get_quantity_in_decision_maker_inbox() -> int
```

Get the quantity of messages in the decision maker inbox.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.get_message_from_decision_maker_inbox"></a>

#### get`_`message`_`from`_`decision`_`maker`_`inbox

```python
def get_message_from_decision_maker_inbox() -> Optional[Message]
```

Get message from decision maker inbox.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.drop_messages_from_decision_maker_inbox"></a>

#### drop`_`messages`_`from`_`decision`_`maker`_`inbox

```python
def drop_messages_from_decision_maker_inbox(number: int = 1) -> None
```

Dismiss the first 'number' number of message from decision maker inbox.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.assert_quantity_in_outbox"></a>

#### assert`_`quantity`_`in`_`outbox

```python
def assert_quantity_in_outbox(expected_quantity: int) -> None
```

Assert the quantity of messages in the outbox.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.assert_quantity_in_decision_making_queue"></a>

#### assert`_`quantity`_`in`_`decision`_`making`_`queue

```python
def assert_quantity_in_decision_making_queue(expected_quantity: int) -> None
```

Assert the quantity of messages in the decision maker queue.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.message_has_attributes"></a>

#### message`_`has`_`attributes

```python
@staticmethod
def message_has_attributes(actual_message: Message,
                           message_type: Type[Message],
                           **kwargs: Any) -> Tuple[bool, str]
```

Evaluates whether a message's attributes match the expected attributes provided.

**Arguments**:

- `actual_message`: the actual message
- `message_type`: the expected message type
- `kwargs`: other expected message attributes

**Returns**:

boolean result of the evaluation and accompanied message

<a id="aea.test_tools.test_skill.BaseSkillTestCase.build_incoming_message"></a>

#### build`_`incoming`_`message

```python
def build_incoming_message(message_type: Type[Message],
                           performative: Message.Performative,
                           dialogue_reference: Optional[Tuple[str,
                                                              str]] = None,
                           message_id: Optional[int] = None,
                           target: Optional[int] = None,
                           to: Optional[Address] = None,
                           sender: Optional[Address] = None,
                           is_agent_to_agent_messages: Optional[bool] = None,
                           **kwargs: Any) -> Message
```

Quickly create an incoming message with the provided attributes.

For any attribute not provided, the corresponding default value in message is used.

**Arguments**:

- `message_type`: the type of the message
- `dialogue_reference`: the dialogue_reference
- `message_id`: the message_id
- `target`: the target
- `performative`: the performative
- `to`: the 'to' address
- `sender`: the 'sender' address
- `is_agent_to_agent_messages`: whether the dialogue is between agents or components
- `kwargs`: other attributes

**Returns**:

the created incoming message

<a id="aea.test_tools.test_skill.BaseSkillTestCase.build_incoming_message_for_skill_dialogue"></a>

#### build`_`incoming`_`message`_`for`_`skill`_`dialogue

```python
def build_incoming_message_for_skill_dialogue(
        dialogue: Dialogue,
        performative: Message.Performative,
        message_type: Optional[Type[Message]] = None,
        dialogue_reference: Optional[Tuple[str, str]] = None,
        message_id: Optional[int] = None,
        target: Optional[int] = None,
        to: Optional[Address] = None,
        sender: Optional[Address] = None,
        **kwargs: Any) -> Message
```

Quickly create an incoming message with the provided attributes for a dialogue.

For any attribute not provided, a value based on the dialogue is used.
These values are shown in parentheses in the list of parameters below.

NOTE: This method must be used with care. The dialogue provided is part of the skill
which is being tested. Because for any unspecified attribute, a "correct" value is used,
the test will be, by design, insured to pass on these values.

**Arguments**:

- `dialogue`: the dialogue to which the incoming message is intended
- `performative`: the performative of the message
- `message_type`: (the message_class of the provided dialogue) the type of the message
- `dialogue_reference`: (the dialogue_reference of the provided dialogue) the dialogue reference of the message
- `message_id`: (the id of the last message in the provided dialogue + 1) the id of the message
- `target`: (the id of the last message in the provided dialogue) the target of the message
- `to`: (the agent address associated with this skill) the receiver of the message
- `sender`: (the counterparty in the provided dialogue) the sender of the message
- `kwargs`: other attributes

**Returns**:

the created incoming message

<a id="aea.test_tools.test_skill.BaseSkillTestCase.prepare_skill_dialogue"></a>

#### prepare`_`skill`_`dialogue

```python
def prepare_skill_dialogue(
        dialogues: Dialogues,
        messages: Tuple[DialogueMessage, ...],
        counterparty: Optional[Address] = None,
        is_agent_to_agent_messages: Optional[bool] = None) -> Dialogue
```

Quickly create a dialogue.

The 'messages' argument is a tuple of DialogueMessages.
For every DialogueMessage (performative, contents, is_incoming, target):
    - if 'is_incoming' is not provided: for the first message it is assumed False (outgoing),
    for any other message, it is the opposite of the one preceding it.
    - if 'target' is not provided: for the first message it is assumed 0,
    for any other message, it is the index of the message before it in the tuple of messages + 1.

**Arguments**:

- `dialogues`: a dialogues class
- `counterparty`: the message_id
- `messages`: the dialogue_reference
- `is_agent_to_agent_messages`: whether the dialogue is between agents or components

**Returns**:

the created incoming message

<a id="aea.test_tools.test_skill.BaseSkillTestCase.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls, **kwargs: Any) -> None
```

Set up the skill test case.

Only called once at the beginning before test methods on the test class are called.

**Arguments**:

- `kwargs`: the keyword arguments passed to _prepare_skill

<a id="aea.test_tools.test_skill.BaseSkillTestCase.setup"></a>

#### setup

```python
def setup(**kwargs: Any) -> None
```

Set up the test method.

Called each time before a test method is called.

**Arguments**:

- `kwargs`: the keyword arguments passed to _prepare_skill

<a id="aea.test_tools.test_skill.BaseSkillTestCase.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Teardown the test method.

Called each time after a test method is called.

<a id="aea.test_tools.test_skill.BaseSkillTestCase.empty_message_queues"></a>

#### empty`_`message`_`queues

```python
def empty_message_queues() -> None
```

Empty message queues

<a id="aea.test_tools.test_skill.BaseSkillTestCase.reset_all_dialogues"></a>

#### reset`_`all`_`dialogues

```python
def reset_all_dialogues() -> None
```

Reset the state of all dialogues

