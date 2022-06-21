<a href="../api/protocols/base#protocol-objects">`Protocols`</a> define the structure of agent-to-agent and component-to-component interactions, which in the AEA world, are in the form of communication. To learn more about interactions and interaction protocols, see <a href="../interaction-protocol">here</a>.

Protocols in the AEA world provide definitions for:

* `messages` defining the structure and syntax of messages;

* `serialization` defining how a message is encoded/decoded for transport; and optionally

* `dialogues` defining the structure of dialogues formed from exchanging series of messages.

<img src="../assets/protocol.svg" alt="Protocol simplified" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">

The framework provides a `base` protocol. This protocol provides a bare-bones implementation for an AEA protocol which includes a <a href="../api/protocols/base/#message-objects" target="_blank">`DefaultMessage`</a>  class and associated <a href="../api/protocols/base/#serializer-objects" target="_blank">`DefaultSerializer`</a> and <a href="../api/protocols/dialogue/base/" target="_blank">`DefaultDialogue`</a> classes.

Additional protocols - i.e. a new type of interaction - can be added as packages or generated with the <a href="../protocol-generator">protocol generator</a>.

We highly recommend you to **not** attempt writing your protocol manually as they tend to have involved logic; always use existing packages or the protocol generator!

## Components of a protocol

A protocol package contains the following files:

* `__init__.py`
* `message.py`, which defines message representation
* `serialization.py`, which defines the encoding and decoding logic
* two protobuf related files

It optionally also contains

* `dialogues.py`, which defines the structure of dialogues formed from the exchange of a series of messages
* `custom_types.py`, which defines custom types

All protocols are for point to point interactions between two agents or agent-like services.

<!-- ## Interaction Protocols

Protocols are not to be conflated with Interaction Protocols. The latter consist of three components in the AEA:

- Protocols: which deal with the syntax and potentially semantics of the message exchange
- Handlers: which handle incoming messages
- Behaviours: which execute pro-active patterns of one-shot, cyclic or even finite-state-machine-like type. -->

## Metadata

Each `Message` in an interaction protocol has a set of default fields:

* `dialogue_reference: Tuple[str, str]`, a reference of the dialogue the message is part of. The first part of the tuple is the reference assigned to by the agent who first initiates the dialogue (i.e. sends the first message). The second part of the tuple is the reference assigned to by the other agent. The default value is `("", "")`.
* `message_id: int`, the identifier of the message in a dialogue. The default value is `1`.
* `target: int`, the id of the message this message is replying to. The default value is `0`.
* `performative: Enum`, the purpose/intention of the message.
* `sender: Address`, the address of the sender of this message.
* `to: Address`, the address of the receiver of this message.

The default values for `message_id` and `target` assume the message is the first message in a dialogue. Therefore, the `message_id` is set to `1` indicating the first message in the dialogue and `target` is `0` since the first message is the only message that does not reply to any other.

By default, the values of `dialogue_reference`, `message_id`, `target` are set. However, most interactions involve more than one message being sent as part of the interaction and potentially multiple simultaneous interactions utilising the same protocol. In those cases, the `dialogue_reference` allows different interactions to be identified as such. The `message_id` and `target` are used to keep track of messages and their replies. For instance, on receiving of a message with `message_id=1` and `target=0`, the responding agent could respond with another with `message_id=2` and `target=1` replying to the first message. In particular, `target` holds the id of the message being replied to. This can be the preceding message, or an older one.

## Contents

Each message may optionally have any number of contents of varying types.

## Dialogue rules

Protocols can optionally have a dialogue module. A _dialogue_, respectively _dialogues_ object, maintains the state of a single, respectively, all dialogues associated with a protocol.

The framework provides a number of helpful classes which implement most of the logic to maintain dialogues, namely the <a href="../api/protocols/dialogue/base#dialogue-objects">`Dialogue`</a> and <a href="../api/protocols/dialogue/base#dialogues-objects">`Dialogues`</a> base classes.

## Custom protocol

The developer can generate custom protocols with the <a href="../protocol-generator">protocol generator</a>. This lets the developer specify the speech-acts as well as optionally the dialogue structure (e.g. roles of agents participating in a dialogue, the states a dialogue may end in, and the reply structure of the speech-acts in a dialogue).

We highly recommend you **do not** attempt to write your own protocol code; always use existing packages or the protocol generator!
