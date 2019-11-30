A `Protocol` manages message representation, encoding, and serialisation. It also defines the rules to which messages must adhere.

An agent can have one or more protocols. The AEA framework supplies three: `oef`, `fipa`, and a `default` protocol.


## Custom protocol

For a custom protocol, the developer must code methods from two classes.

### `Message.check_consistency(self)`

This method checks the message data for consistency and raises an error if necessary.

!!! TODO
    For example.

### `Serializer.encode(self, msg: Message)`

This method encodes a message object into bytes for passing around.

!!! TODO
    For example.

### `Serializer.decode(self, obj: bytes)`

This method decodes the byte representation of a message object.

!!! TODO
    For example.

Outside of these, the developer is free to implement the agent protocols in any way they see fit.

### `rules.py`

!!! Note
    Coming soon.



## `oef` protocol

The `oef` helps agents to search for and find other agents and (for now) talk to them via different protocols. 

!!! Note
    In future, the framework will support peer to peer communications.

The `oef` protocol definition includes an `OEFMessage` class which gets a `protocol_id` of `oef`.

It defines OEF agent delegation by way of a `MessageType` Enum.

``` python
class Type(Enum):
	
	"""OEF Message types."""
    REGISTER_SERVICE = "register_service"
    UNREGISTER_SERVICE = "unregister_service"
    SEARCH_SERVICES = "search_services"
    SEARCH_AGENTS = "search_agents"
    OEF_ERROR = "oef_error"
    DIALOGUE_ERROR = "dialogue_error"
    SEARCH_RESULT = "search_result"

    def __str__(self):
    	"""Get string representation."""
        return self.value
```
It also provides error codes.

``` python
class OEFErrorOperation(Enum):
        
	"""Operation code for the OEF. It is returned in the OEF Error messages."""
	REGISTER_SERVICE = 0
    UNREGISTER_SERVICE = 1
    SEARCH_SERVICES = 2
    SEARCH_SERVICES_WIDE = 3
    SEARCH_AGENTS = 4
    SEND_MESSAGE = 5

    OTHER = 10000
```
A `models.py` module is provided by the `oef` protocol which includes classes and methods commonly required by OEF agents. These includes a class for serialising json and classes for implementing the OEF query language such as `Attribute`, `Query`, etc. 




## `fipa` protocol

The `fipa` protocol definition includes a `FIPAMessage` class which gets a `protocol_id` of `fipa`.

It defines FIPA negotiating terms by way of a `Performative(Enum)`.

``` python
class Performative(Enum):
	
	"""FIPA performatives."""
	CFP = "cfp"
    PROPOSE = "propose"
    ACCEPT = "accept"
    MATCH_ACCEPT = "match_accept"
    DECLINE = "decline"

    def __str__(self):
    	"""Get string representation."""
        return self.value
```

`FIPAMessages` are constructed with a `message_id`, a `dialogue_id`, a `target` and `peformative`.

``` python
super().__init__(id=message_id, dialogue_id=dialogue_id, target=target, 
	performative=FIPAMessage.Performative(performative), **kwargs)
```
The `fipa.proto` file then further qualifies the performatives for `protobuf` messaging.

``` java
syntax = "proto3";

package fetch.aea.fipa;

message FIPAMessage{

    message CFP{
        message Nothing {
        }
        oneof query{
            bytes bytes = 2;
            Nothing nothing = 3;
        }
    }
    message Propose{
        repeated bytes proposal = 4;
    }
    message Accept{}
    message MatchAccept{}
    message Decline{}

    int32 message_id = 1;
    int32 dialogue_id = 2;
    int32 target = 3;
    oneof performative{
        CFP cfp = 4;
        Propose propose = 5;
        Accept accept = 6;
        MatchAccept match_accept = 7;
        Decline decline = 8;
    }
}
```


## `default` protocol

The `default` protocol has a `DefaultMessage` class which gets a `protocol_id` of `default`.

It has two message types: `BYTES` and `ERROR`, and provides error messages for the error skill which uses it.

The serialisation methods `encode` and `decode` implement transformations from `Message` type to bytes and back.









<br />
