<a id="aea.test_tools.test_protocol"></a>

# aea.test`_`tools.test`_`protocol

This module contains test case classes based on pytest for AEA protocol testing.

<a id="aea.test_tools.test_protocol.BaseProtocolMessagesTestCase"></a>

## BaseProtocolMessagesTestCase Objects

```python
class BaseProtocolMessagesTestCase(ABC)
```

Base class to test messages for the protocol.

<a id="aea.test_tools.test_protocol.BaseProtocolMessagesTestCase.MESSAGE_CLASS"></a>

#### MESSAGE`_`CLASS

```python
@property
@abstractmethod
def MESSAGE_CLASS() -> Type[Message]
```

Override this property in a subclass.

<a id="aea.test_tools.test_protocol.BaseProtocolMessagesTestCase.perform_message_test"></a>

#### perform`_`message`_`test

```python
def perform_message_test(msg: Message) -> None
```

Test message encode/decode.

<a id="aea.test_tools.test_protocol.BaseProtocolMessagesTestCase.test_messages_ok"></a>

#### test`_`messages`_`ok

```python
def test_messages_ok() -> None
```

Run messages are ok for encode and decode.

<a id="aea.test_tools.test_protocol.BaseProtocolMessagesTestCase.test_messages_inconsistent"></a>

#### test`_`messages`_`inconsistent

```python
def test_messages_inconsistent() -> None
```

Run messages are inconsistent.

<a id="aea.test_tools.test_protocol.BaseProtocolMessagesTestCase.test_messages_fail_to_encode_decode"></a>

#### test`_`messages`_`fail`_`to`_`encode`_`decode

```python
def test_messages_fail_to_encode_decode() -> None
```

Run messages are failing to encode and decode.

<a id="aea.test_tools.test_protocol.BaseProtocolMessagesTestCase.build_messages"></a>

#### build`_`messages

```python
@abstractmethod
def build_messages() -> List[Message]
```

Build the messages to be used for testing.

<a id="aea.test_tools.test_protocol.BaseProtocolMessagesTestCase.build_inconsistent"></a>

#### build`_`inconsistent

```python
@abstractmethod
def build_inconsistent() -> List[Message]
```

Build inconsistent messages to be used for testing.

<a id="aea.test_tools.test_protocol.BaseProtocolDialoguesTestCase"></a>

## BaseProtocolDialoguesTestCase Objects

```python
class BaseProtocolDialoguesTestCase(ABC)
```

Base class to test message construction for the protocol.

<a id="aea.test_tools.test_protocol.BaseProtocolDialoguesTestCase.MESSAGE_CLASS"></a>

#### MESSAGE`_`CLASS

```python
@property
@abstractmethod
def MESSAGE_CLASS() -> Type[Message]
```

Override this property in a subclass.

<a id="aea.test_tools.test_protocol.BaseProtocolDialoguesTestCase.DIALOGUE_CLASS"></a>

#### DIALOGUE`_`CLASS

```python
@property
@abstractmethod
def DIALOGUE_CLASS() -> Type[Dialogue]
```

Override this property in a subclass.

<a id="aea.test_tools.test_protocol.BaseProtocolDialoguesTestCase.DIALOGUES_CLASS"></a>

#### DIALOGUES`_`CLASS

```python
@property
@abstractmethod
def DIALOGUES_CLASS() -> Type[Dialogues]
```

Override this property in a subclass.

<a id="aea.test_tools.test_protocol.BaseProtocolDialoguesTestCase.ROLE_FOR_THE_FIRST_MESSAGE"></a>

#### ROLE`_`FOR`_`THE`_`FIRST`_`MESSAGE

```python
@property
@abstractmethod
def ROLE_FOR_THE_FIRST_MESSAGE() -> Dialogue.Role
```

Override this property in a subclass.

<a id="aea.test_tools.test_protocol.BaseProtocolDialoguesTestCase.role_from_first_message"></a>

#### role`_`from`_`first`_`message

```python
def role_from_first_message(message: Message,
                            receiver_address: Address) -> Dialogue.Role
```

Infer the role of the agent from an incoming/outgoing first message

**Arguments**:

- `message`: an incoming/outgoing first message
- `receiver_address`: the address of the receiving agent

**Returns**:

The role of the agent

<a id="aea.test_tools.test_protocol.BaseProtocolDialoguesTestCase.make_dialogues_class"></a>

#### make`_`dialogues`_`class

```python
def make_dialogues_class() -> Type[Dialogues]
```

Make dialogues class with specific role.

<a id="aea.test_tools.test_protocol.BaseProtocolDialoguesTestCase.make_message_content"></a>

#### make`_`message`_`content

```python
@abstractmethod
def make_message_content() -> dict
```

Make a dict with message contruction content for dialogues.create.

<a id="aea.test_tools.test_protocol.BaseProtocolDialoguesTestCase.test_dialogues"></a>

#### test`_`dialogues

```python
def test_dialogues() -> None
```

Test dialogues.

