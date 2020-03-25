A `Protocol` manages message representation (syntax, `message.py`), optionally rules of the message exchange (semantics, `dialogues.py`), as well as encoding, and decoding (`serialization.py`). All protocols are for point to point interaction between two agents. Agents can be AEAs or other types of agent-like services.

<!-- ## Interaction Protocols

Protocols are not to be conflated with Interaction Protocols. The latter consist of three components in the AEA:

- Protocols: which deal with the syntax and potentially semantics of the message exchange
- Handlers: which handle incoming messages
- Behaviours: which execute pro-active patterns of one-shot, cyclic or even finite-state-machine-like type. -->

## Metadata

Each `Message` in an interaction protocol has a set of default metadata, this includes:

* `dialogue_reference: Tuple[str, str]`, a reference of the dialogue the message is part of. The first part of the tuple is the reference assigned to by the dialogue initiator, the second part of the tuple is the reference assigned to by the dialogue responder. The default value is `("", "")`.
* `message_id: int`, the id of the message. The default value is `1`.
* `target: int`, the id of the message which is referenced by this message. The default value is `0`.

By default, `dialogue_reference`, `message_id` and `target` are set, however, most interactions involve more than one message being sent as part of the interaction and potentially multiple simultaneous interactions utilising the same protocol. In those cases, the `dialogue_reference` allows different interactions to be identified as such. The `message_id` and `target` are used to keep reference to the preceding messages in a dialogue for a given interaction. For instance, following receipt of a message with `target=0` and `message_id=1` the responding AEA should respond with a `message_id=2` and `target=1`. In particular, `target` holds the id of the message being referenced. This can be the preceding message, it can also be an older message. Hence, `0 < target < message_id` for `message_id > 1` and `target=0` if `message_id = 1`. 

## Custom protocol

The developer can generate custom protocols with the <a href="../protocol-generator">protocol generator</a>. 

## `fetchai/default:0.1.0` protocol

The `fetchai/default:0.1.0` protocol is a protocol which each AEA is meant to implement. It serves AEA to AEA interaction and includes two message performatives:

``` python
class Performative(Enum):
    """Performatives for the default protocol."""

    BYTES = "bytes"
    ERROR = "error"

    def __str__(self):
        """Get the string representation."""
        return self.value
```

* The `DefaultMessage` of performative `DefaultMessage.Performative.BYTES` is used to send payloads of byte strings to other AEAs. An example is:
``` python
msg = DefaultMessage(
    performative=DefaultMessage.Performative.BYTES,
    content=b"This is a bytes payload",
)
```

* The `DefaultMessage` of performative `DefaultMessage.Performative.ERROR` is used to notify other AEAs of errors in an interaction, including errors with other protocols, by including an `error_code` in the payload:
``` python
class ErrorCode(Enum):
    """This class represents an instance of ErrorCode."""

    UNSUPPORTED_PROTOCOL = 0
    DECODING_ERROR = 1
    INVALID_MESSAGE = 2
    UNSUPPORTED_SKILL = 3
    INVALID_DIALOGUE = 4
```
An example is:
``` python
msg = DefaultMessage(
    performative=DefaultMessage.Performative.ERROR,
    error_code=DefaultMessage.ErrorCode.UNSUPPORTED_PROTOCOL,
    error_msg="This protocol is not supported by this AEA.",
    error_data={"unsupported_msg": b"serialized unsupported protocol message"},
)
```

Each AEA's `fetchai/error:0.1.0` skill utilises the `fetchai/default:0.1.0` protocol for error handling.

## `fetchai/oef_search:0.1.0` protocol

The `fetchai/oef_search:0.1.0` protocol is used by AEAs to interact with an [OEF search node](../oef-ledger) to register and unregister their own services and search for services registered by other agents.

The `fetchai/oef_search:0.1.0` protocol definition includes an `OefSearchMessage` with the following message types:

```python
class Performative(Enum):

	"""Performatives for the oef_search protocol."""
    REGISTER_SERVICE = "register_service"
    UNREGISTER_SERVICE = "unregister_service"
    SEARCH_SERVICES = "search_services"
    OEF_ERROR = "oef_error"
    SEARCH_RESULT = "search_result"

    def __str__(self):
    	"""Get string representation."""
        return self.value
```

We show some example messages below:

* To register a service, we require a reference to the dialogue in string form (used to keep different dialogues apart), for instance
``` python
my_dialogue_reference = "a_unique_register_service_dialogue_reference"
```
and a description of the service we would like to register, for instance
```python
my_service_data = {"country": "UK", "city": "Cambridge"}
my_service_description = Description(
    my_service_data,
    data_model=my_data_model,
)
```
where we use, for instance
``` python
from aea.helpers.search.generic import GenericDataModel

data_model_name = "location"
data_model = {
    "attribute_one": {
        "name": "country",
        "type": "str",
        "is_required": "True",
    },
    "attribute_two": {
        "name": "city",
        "type": "str",
        "is_required": "True",
    },
}
my_data_model = GenericDataModel(data_model_name, data_model)
```
We can then create the message to register this service:
``` python
msg = OefSearchMessage(
    performative=OefSearchMessage.Performative.REGISTER_SERVICE,
    dialogue_reference=(my_dialogue_reference, ""),
    service_description=my_service_description,
)
```

* To unregister a service, we require a reference to the dialogue in string form, for instance
``` python
my_dialogue_reference = "a_unique_unregister_service_dialogue_reference"
```
the description of the service we would like to unregister, say `my_service_description` from above and construct the message:
``` python
msg = OefSearchMessage(
    performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
    dialogue_reference=(my_dialogue_reference, ""),
    service_description=my_service_description,
)
```

* To search a service, we require a reference to the dialogue in string form, for instance
``` python
my_dialogue_reference = "a_unique_search_dialogue_reference"
```
and a query we would like the search node to evaluate, for instance
``` python
from aea.helpers.search.models import Constraint, ConstraintType, Query

query_data = {
    "search_term": "country",
    "search_value": "UK",
    "constraint_type": "==",
}
query = Query(
    [
        Constraint(
            query_data["search_term"],
            ConstraintType(
                query_data["constraint_type"],
                query_data["search_value"],
            ),
        )
    ],
    model=None,
)
```
We can then create the message to search these services:
``` python
oef_msg = OefSearchMessage(
    performative=OefSearchMessage.Performative.SEARCH_SERVICES,
    dialogue_reference=(my_dialogue_reference, ""),
    query=query,
)
```

* The [OEF search node](../oef-ledger) will respond with a message, say `msg` of type `OefSearchMessage`, of performative `OefSearchMessage.Performative.SEARCH_RESULT`. To access the tuple of agents which match the query, simply use `msg.agents`. In particular, this will return the agent addresses matching the query. The [agent address](../identity) can then be used to send a message to the agent utilising the [OEF communication node](../oef-ledger) and any protocol other than `fetchai/oef_search:0.1.0`.

* If the [OEF search node](../oef-ledger) encounters any errors with the messages you send, it will return an `OefSearchMessage` of performative `OefSearchMessage.Performative.OEF_ERROR` and indicate the error operation encountered:
```python
class OefErrorOperation(Enum):

	"""This class represents an instance of OefErrorOperation."""
	REGISTER_SERVICE = 0
    UNREGISTER_SERVICE = 1
    SEARCH_SERVICES = 2
    SEND_MESSAGE = 3

    OTHER = 10000
```

## `fetchai/fipa:0.1.0` protocol

The `fetchai/fipa:0.1.0` protocol definition includes a `FipaMessage` with the following performatives:

```python
class Performative(Enum):
    """Performatives for the fipa protocol."""

    ACCEPT = "accept"
    ACCEPT_W_INFORM = "accept_w_inform"
    CFP = "cfp"
    DECLINE = "decline"
    INFORM = "inform"
    MATCH_ACCEPT = "match_accept"
    MATCH_ACCEPT_W_INFORM = "match_accept_w_inform"
    PROPOSE = "propose"

    def __str__(self):
    	"""Get string representation."""
        return self.value
```

`FipaMessages` are constructed with a `performative`, `dialogue_reference`, `message_id`, and `target` as well as the `kwargs` specific to each message performative.

```python
def __init__(
    self,
    performative: Performative,
    dialogue_reference: Tuple[str, str] = ("", ""),
    message_id: int = 1,
    target: int = 0,
    **kwargs,
)
```

For examples of the usage of the `fetchai/fipa:0.1.0` protocol check out the <a href="../thermometer-skills-step-by-step" target=_blank> thermometer skill step by step guide</a>.



<br />
