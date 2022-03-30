<a id="aea.test_tools.test_skill"></a>

# aea.test`_`tools.test`_`skill

This module contains test case classes based on pytest for AEA skill testing.

<a id="aea.test_tools.test_skill.BaseSkillTestCase"></a>

## BaseSkillTestCase Objects

```python
class BaseSkillTestCase()
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

