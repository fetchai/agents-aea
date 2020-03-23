A `Protocol` manages message representation, encoding, and serialisation. It also defines the rules to which messages must adhere.

An AEA can have one or more protocols. The AEA framework supplies the `fetchai/default:0.1.0` protocol.

## Interaction Protocols

Protocols are not to be conflated with Interaction Protocols. The latter consist of three components in the AEA:

- Protocols: which deal with the syntax and potentially semantics of the message exchange
- Handlers: which handle incoming messages
- Behaviours: which execute pro-active patterns of one-shot, cyclic or even finite-state-machine-like type.

## Custom protocol

The developer can generate custom protocols with the <a href="../protocol-generator">protocol generator</a>. 

## `fetchai/default:0.1.0` protocol

The `default` protocol has two message performatives: `BYTES` and `ERROR`, and provides error messages for the error skill which uses it.

The serialisation methods `encode` and `decode` implement transformations from `Message` type to bytes and back.

## `fetchai/oef:0.1.0` protocol

The `fetchai/oef:0.1.0` protocol is used by AEAs to register and unregister their own services and search for services registered by other agents.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>In future, the framework will support peer to peer communications.</p>
</div>

The `oef` protocol definition includes an `OefMessage` with the following message types:

```python
class Type(Enum):

	"""OEF Message types."""
    REGISTER_SERVICE = "register_service"
    UNREGISTER_SERVICE = "unregister_service"
    SEARCH_SERVICES = "search_services"
    OEF_ERROR = "oef_error"
    SEARCH_RESULT = "search_result"

    def __str__(self):
    	"""Get string representation."""
        return self.value
```

It also provides error codes.

```python
class OefErrorOperation(Enum):

	"""Operation code for the OEF. It is returned in the OEF Error messages."""
	REGISTER_SERVICE = 0
    UNREGISTER_SERVICE = 1
    SEARCH_SERVICES = 2
    SEARCH_SERVICES_WIDE = 3
    SEND_MESSAGE = 4

    OTHER = 10000
```

## `fetchai/fipa:0.1.0` protocol

The `fetchai/fipa:0.1.0` protocol definition includes a `FIPAMessage` with the following performatives:

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

`FIPAMessages` are constructed with a `message_id`, a `dialogue_id`, a `target` and `peformative`.

```python
super().__init__(
    message_id=message_id,
    dialogue_reference=dialogue_reference,
    target=target,
    performative=FIPAMessage.Performative(performative),
    **kwargs
)
```

The `fipa.proto` file then further qualifies the performatives for `protobuf` messaging.

``` proto
syntax = "proto3";

package fetch.aea.fipa;

message FIPAMessage{

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
