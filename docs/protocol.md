A `Protocol` manages message representation (syntax in `message.py`), optionally rules of the message exchange (semantics in `dialogues.py`), as well as encoding and decoding (in `serialization.py`). All protocols are for point to point interactions between two agents. Agents can be AEAs or other types of agent-like services.

<!-- ## Interaction Protocols

Protocols are not to be conflated with Interaction Protocols. The latter consist of three components in the AEA:

- Protocols: which deal with the syntax and potentially semantics of the message exchange
- Handlers: which handle incoming messages
- Behaviours: which execute pro-active patterns of one-shot, cyclic or even finite-state-machine-like type. -->

## Metadata

Each `Message` in an interaction protocol has a set of default fields:

* `dialogue_reference: Tuple[str, str]`, a reference of the dialogue the message is part of. The first part of the tuple is the reference assigned to by the agent who first initiates the dialogue (i.e. sends the first message). The second part of the tuple is the reference assigned to by the other agent. * `dialogue_reference: Tuple[str, str]`, a reference of the dialogue the message is part of. The first part of the tuple is the reference assigned to by the dialogue initiator, the second part of the tuple is the reference assigned to by the dialogue responder. The default value is `("", "")`.
* `message_id: int`, the identifier of the message in a dialogue. The default value is `1`.
* `target: int`, the id of the message this message is replying to. The default value is `0`.
* `Performative: Enum`, the purpose/intention of the message. 
* `is_incoming: bool`, a boolean specifying whether the message is outgoing (from the agent), or incoming (from the other agent). The default value is `False`. 
* `counterparty: Address`, the address of the counterparty of this agent; the other agent, this agent is communicating with.  

The default values for the above fields assume the message is the first message by the agent in a dialogue. Therefore, the `message_id` is set to `1` indicating the first message in the dialogue, `target` is `0` since the first  message is the only message that does not reply to any other, and `is_incoming` is `False` indicating the message is by the agent itself.

By default, the values of `dialogue_reference`, `message_id`, `target`, `is_incoming`, `counterparty` are set. However, most interactions involve more than one message being sent as part of the interaction and potentially multiple simultaneous interactions utilising the same protocol. In those cases, the `dialogue_reference` allows different interactions to be identified as such. The `message_id` and `target` are used to keep track of messages and their replies. For instance, on receiving of a message with `message_id=1` and `target=0`, the responding agent could respond with a another with `message_id=2` and `target=1` replying to the first message. In particular, `target` holds the id of the message being replied to. This can be the preceding message, or an older one. 

## Contents

Each message may optionally have any number of contents of varying types. 

## Dialogue rules

Protocols can optionally have a dialogue module. A _dialogue_, respectively _dialogues_ object, maintains the state of a single dialogue, respectively all dialogues, associated with the protocol. 

## Custom protocol

The developer can generate custom protocols with the <a href="../protocol-generator">protocol generator</a>. This lets the developer specify the speech-acts as well as optionally the dialogue structure (e.g. roles of agents participating in a dialogue, the states a dialogue may end in, and the reply structure of the speech-acts in a dialogue).

## `fetchai/default:0.1.0` protocol

The `fetchai/default:0.1.0` protocol is a protocol which each AEA is meant to implement. It serves AEA to AEA interaction and includes two message performatives:

``` python
from enum import Enum

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
from aea.protocols.default.message import DefaultMessage

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

Each AEA's `fetchai/error:0.2.0` skill utilises the `fetchai/default:0.1.0` protocol for error handling.

## `fetchai/oef_search:0.1.0` protocol

The `fetchai/oef_search:0.1.0` protocol is used by AEAs to interact with an [OEF search node](../oef-ledger) to register and unregister their own services and search for services registered by other agents.

The `fetchai/oef_search:0.1.0` protocol definition includes an `OefSearchMessage` with the following message types:

``` python
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
from aea.helpers.search.models import Description

my_service_data = {"country": "UK", "city": "Cambridge"}
my_service_description = Description(
    my_service_data,
    data_model=my_data_model,
)
```
where we use, for instance
```python
from aea.helpers.search.generic import GenericDataModel

data_model_name = "location"
data_model = {
    "attribute_one": {
        "name": "country",
        "type": "str",
        "is_required": True,
    },
    "attribute_two": {
        "name": "city",
        "type": "str",
        "is_required": True,
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
``` python
class OefErrorOperation(Enum):

    """This class represents an instance of OefErrorOperation."""
    REGISTER_SERVICE = 0
    UNREGISTER_SERVICE = 1
    SEARCH_SERVICES = 2
    SEND_MESSAGE = 3

    OTHER = 10000
```

## `fetchai/fipa:0.2.0` protocol

The `fetchai/fipa:0.2.0` protocol definition includes a `FipaMessage` with the following performatives:

``` python
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
        """Get the string representation."""
        return self.value
```

`FipaMessages` are constructed with a `performative`, `dialogue_reference`, `message_id`, and `target` as well as the `kwargs` specific to each message performative.

``` python
def __init__(
    self,
    performative: Performative,
    dialogue_reference: Tuple[str, str] = ("", ""),
    message_id: int = 1,
    target: int = 0,
    **kwargs,
)
```

The `fetchai/fipa:0.2.0` protocol also defines a `FipaDialogue` class which specifies the valid reply structure and provides other helper methods to maintain dialogues.

For examples of the usage of the `fetchai/fipa:0.2.0` protocol check out the <a href="../thermometer-skills-step-by-step" target=_blank> thermometer skill step by step guide</a>.



<br />
