A `Protocol` manages message representation, encoding, and serialisation. It also defines the rules to which messages must adhere.

An AEA can have one or more protocols. The AEA framework supplies the `fetchai/default:0.1.0` protocol.

## Interaction Protocols

Protocols are not to be conflated with Interaction Protocols. The latter consist of three components in the AEA:

- Protocols: which deal with the syntax and potentially semantics of the message exchange
- Handlers: which handle incoming messages
- Behaviours: which execute pro-active patterns of one-shot, cyclic or even finite-state-machine-like type.

## Metadata

Each `Message` in an interaction protocol has a set of default metadata, this includes:

* `dialogue_reference: Tuple[str, str]`, a reference of the dialogue the message is part of. The first part of the tuple is the reference assigned to by the dialogue initiator, the second part of the tuple is the reference assigned to by the dialogue responder. The default value is `("", "")`.
* `message_id: int`, the id of the message. The default value is `1`.
* `target: int`, the id of the message which is referenced by this message. The default value is `0`.

## Custom protocol

The developer can generate custom protocols with the <a href="../protocol-generator">protocol generator</a>. 

## `fetchai/default:0.1.0` protocol

The `default` protocol has two message performatives: `BYTES` and `ERROR`, and provides error messages for the error skill which uses it.

The serialisation methods `encode` and `decode` implement transformations from `Message` type to bytes and back.

## `fetchai/oef_search:0.1.0` protocol

The `fetchai/oef_search:0.1.0` protocol is used by AEAs to register and unregister their own services and search for services registered by other agents.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>In future, the framework will support peer to peer communications.</p>
</div>

The `oef` protocol definition includes an `OefSearchMessage` with the following message types:

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

* To register a service, we require a reference to the dialogue in string form, for instance
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

* The [OEF search node](../oef-ledger) will respond with a message, say `msg` of type `OefSearchMessage`, of performative `OefSearchMessage.Performative.SEARCH_RESULT`. To access the tuple of agents which match the query, simply use `msg.agents`. In particular, this will return the agent addresses matching the query. The [agent address](../identity) can then be used to send a message to the agent utilising the [OEF communication node](../oef-ledger).

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

	"""FIPA performatives."""
    CFP = "cfp"
    PROPOSE = "propose"
    ACCEPT = "accept"
    MATCH_ACCEPT = "match_accept"
    DECLINE = "decline"
    INFORM = "inform"
    ACCEPT_W_INFORM = "accept_w_inform"
    MATCH_ACCEPT_W_INFORM = "match_accept_w_inform"

    def __str__(self):
    	"""Get string representation."""
        return self.value
```

`FipaMessages` are constructed with a `message_id`, a `dialogue_id`, a `target` and `peformative`.

```python
super().__init__(
    message_id=message_id,
    dialogue_reference=dialogue_reference,
    target=target,
    performative=FipaMessage.Performative(performative),
    **kwargs
)
```

The `fipa.proto` file then further qualifies the performatives for `protobuf` messaging.

``` proto
syntax = "proto3";

package fetch.aea.fipa;

message FipaMessage{

    message CFP{
        message Nothing {
        }
        oneof query{
            bytes bytes = 1;
            Nothing nothing = 2;
            bytes query_bytes = 3;
        }
    }
    message Propose{
        repeated bytes proposal = 1;
    }
    message Accept{}

    message MatchAccept{}

    message Decline{}

    message Inform{
        bytes bytes = 1;
    }

    message AcceptWInform{
        bytes bytes = 1;
    }

    message MatchAcceptWInform{
        bytes bytes = 1;
    }

    int32 message_id = 1;
    string dialogue_starter_reference = 2;
    string dialogue_responder_reference = 3;
    int32 target = 4;
    oneof performative{
        CFP cfp = 5;
        Propose propose = 6;
        Accept accept = 7;
        MatchAccept match_accept = 8;
        Decline decline = 9;
        Inform inform = 10;
        AcceptWInform accept_w_inform = 11;
        MatchAcceptWInform match_accept_w_inform = 12;
    }
}
```



<br />
