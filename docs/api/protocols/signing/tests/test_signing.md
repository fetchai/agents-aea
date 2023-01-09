<a id="packages.open_aea.protocols.signing.tests.test_signing"></a>

# packages.open`_`aea.protocols.signing.tests.test`_`signing

This module contains tests for transaction.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestMessages"></a>

## TestMessages Objects

```python
class TestMessages(BaseProtocolMessagesTestCase)
```

Base class to test message construction for the protocol.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestMessages.build_messages"></a>

#### build`_`messages

```python
def build_messages() -> List[SigningMessage]
```

Build the messages to be used for testing.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestMessages.build_inconsistent"></a>

#### build`_`inconsistent

```python
def build_inconsistent() -> List[SigningMessage]
```

Build inconsistent messages to be used for testing.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestDialogues"></a>

## TestDialogues Objects

```python
class TestDialogues(BaseProtocolDialoguesTestCase)
```

Test dialogues.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestDialogues.make_message_content"></a>

#### make`_`message`_`content

```python
def make_message_content() -> dict
```

Make a dict with message contruction content for dialogues.create.

