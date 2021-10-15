<a href="../api/protocols/base#protocol-objects">`Protocols`</a> define the structure of agent-to-agent and component-to-component interactions, which in the AEA world, are in the form of communication. To learn more about interactions and interaction protocols, see <a href="../interaction-protocol">here</a>. 

Protocols in the AEA world provide definitions for:

* `messages` defining the structure and syntax of messages;

* `serialization` defining how a message is encoded/decoded for transport; and optionally

* `dialogues` defining the structure of dialogues formed from exchanging series of messages.

<img src="../assets/protocol.jpg" alt="Protocol simplified" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">

The framework provides a `default` protocol. This protocol provides a bare-bones implementation for an AEA protocol which includes a <a href="../api/protocols/default/message#packages.fetchai.protocols.default.message">`DefaultMessage`</a>  class and associated <a href="../api/protocols/default/serialization#packages.fetchai.protocols.default.serialization">`DefaultSerializer`</a> and <a href="../api/protocols/default/dialogues#packages.fetchai.protocols.default.dialogues">`DefaultDialogue`</a> classes.

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

## `fetchai/default:1.0.0` protocol

The `fetchai/default:1.0.0` protocol is meant to be implemented by every AEA. It serves AEA to AEA interaction and includes three message performatives:

``` python
from enum import Enum

class Performative(Enum):
    """Performatives for the default protocol."""

    BYTES = "bytes"
    END = "end"
    ERROR = "error"

    def __str__(self):
        """Get the string representation."""
        return self.value
```

* The `DefaultMessage` of performative `DefaultMessage.Performative.BYTES` is used to send payloads of byte strings to other AEAs. An example is:
``` python
from packages.fetchai.protocols.default.message import DefaultMessage

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

* The `DefaultMessage` of performative `DefaultMessage.Performative.END` is used to terminate a default protocol dialogue. An example is:
``` python
from packages.fetchai.protocols.default.message import DefaultMessage

msg = DefaultMessage(
    performative=DefaultMessage.Performative.END,
)
```

Each AEA's `fetchai/error:0.17.0` skill utilises the `fetchai/default:1.0.0` protocol for error handling.

## `fetchai/oef_search:1.0.0` protocol

The `fetchai/oef_search:1.0.0` protocol is used by AEAs to interact with an <a href="../simple-oef">SOEF search node</a> to register and unregister their own services and search for services registered by other agents.

The `fetchai/oef_search:1.0.0` protocol definition includes an `OefSearchMessage` with the following message types:

``` python
class Performative(Enum):

    """Performatives for the oef_search protocol."""
    REGISTER_SERVICE = "register_service"
    UNREGISTER_SERVICE = "unregister_service"
    SEARCH_SERVICES = "search_services"
    OEF_ERROR = "oef_error"
    SEARCH_RESULT = "search_result"
    SUCCESS = "success"

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
``` python
from aea.helpers.search.models import Description

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

* To search a service, we similarly require a reference to the dialogue in string form, and then the query we would like the search node to evaluate, for instance
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

* The <a href="../simple-oef">SOEF search node</a> will respond with a message `msg` of type `OefSearchMessage` with performative `OefSearchMessage.Performative.SEARCH_RESULT`. To access the tuple of agents which match the query, simply use `msg.agents`. In particular, this will return the agent addresses matching the query. The <a href="../identity">agent address</a> can then be used to send a message to the agent utilising the <a href="../oef-ledger">P2P agent communication network</a> and any protocol other than `fetchai/oef_search:1.0.0`.

* If the <a href="../simple-oef">SOEF search node</a> encounters any errors with the messages you send, it will return an `OefSearchMessage` of performative `OefSearchMessage.Performative.OEF_ERROR` and indicate the error operation encountered:
``` python
class OefErrorOperation(Enum):

    """This class represents an instance of OefErrorOperation."""
    REGISTER_SERVICE = 0
    UNREGISTER_SERVICE = 1
    SEARCH_SERVICES = 2
    SEND_MESSAGE = 3

    OTHER = 10000
```

## `fetchai/fipa:1.0.0` protocol

This protocol provides classes and functions necessary for communication between AEAs via a variant of the <a href="https://en.wikipedia.org/wiki/Foundation_for_Intelligent_Physical_Agents" target="_blank">FIPA</a> Agent Communication Language.

The `fetchai/fipa:1.0.0` protocol definition includes a `FipaMessage` with the following performatives:

``` python
class Performative(Enum):
    """Performatives for the fipa protocol."""

    ACCEPT = "accept"
    ACCEPT_W_INFORM = "accept_w_inform"
    CFP = "cfp"
    DECLINE = "decline"
    END = "end"
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

The `fetchai/fipa:1.0.0` protocol also defines a `FipaDialogue` class which specifies the valid reply structure and provides other helper methods to maintain dialogues.

For examples of the usage of the `fetchai/fipa:1.0.0` protocol check out the <a href="../generic-skills-step-by-step" target="_blank"> generic skills step by step guide</a>.


### Fipa dialogue

Below, we give an example of a dialogue between two agents. In practice; both dialogues would be maintained in the respective agent.

We first create concrete implementations of `FipaDialogue` and `FipaDialogues` for the buyer and seller:
``` python
from aea.common import Address
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage


class BuyerDialogue(FipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[FipaMessage] = FipaMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        FipaDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self.proposal = None  # type: Optional[Description]


class BuyerDialogues(FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        def role_from_first_message(
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseFipaDialogue.Role.BUYER

        FipaDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=FipaDialogue,
        )


class SellerDialogue(FipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[FipaMessage] = FipaMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        FipaDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self.proposal = None  # type: Optional[Description]


class SellerDialogues(FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        def role_from_first_message(
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return FipaDialogue.Role.SELLER

        FipaDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=FipaDialogue,
        )
```

Next, we can imitate a dialogue between the buyer and the seller. We first instantiate the dialogues models:
``` python
buyer_address = "buyer_address_stub"
seller_address = "seller_address_stub"
buyer_dialogues = BuyerDialogues(buyer_address)
seller_dialogues = SellerDialogues(seller_address)
```

First, the buyer creates a message destined for the seller and updates the dialogues:
``` python
cfp_msg = FipaMessage(
    message_id=1,
    dialogue_reference=buyer_dialogues.new_self_initiated_dialogue_reference(),
    target=0,
    performative=FipaMessage.Performative.CFP,
    query=Query([Constraint("something", ConstraintType(">", 1))]),
)
cfp_msg.counterparty = seller_addr

# Extends the outgoing list of messages.
buyer_dialogue = buyer_dialogues.update(cfp_msg)
```
If the message has been correctly constructed, the `buyer_dialogue` will be returned, otherwise it will be `None`.

In a skill, the message could now be sent:
``` python
# In a skill we would do:
# self.context.outbox.put_message(message=cfp_msg)
```

However, here we simply continue with the seller:
``` python
# change the incoming message field & counterparty
cfp_msg.is_incoming = True
cfp_msg.counterparty = buyer_address
```
In the skill, the above two lines will be done by the framework; you can simply receive the message in the handler.

We update the seller's dialogues model next to generate a new dialogue:
``` python
# Creates a new dialogue for the seller side based on the income message.
seller_dialogue = seller_dialogues.update(cfp_msg)
```

Next, the seller can generate a proposal:
``` python
# Generate a proposal message to send to the buyer.
proposal = Description({"foo1": 1, "bar1": 2})
message_id = cfp_msg.message_id + 1
target = cfp_msg.message_id
proposal_msg = FipaMessage(
    message_id=message_id,
    dialogue_reference=seller_dialogue.dialogue_label.dialogue_reference,
    target=target,
    performative=FipaMessage.Performative.PROPOSE,
    proposal=proposal,
)
proposal_msg.counterparty = cfp_msg.counterparty

# Then we update the dialogue
seller_dialogue.update(proposal_msg)
```

In a skill, the message could now be sent:
``` python
# In a skill we would do:
# self.context.outbox.put_message(message=proposal_msg)
```

The dialogue can continue like this.

To retrieve a dialogue for a given message, we can do the following:

``` python
retrieved_dialogue = seller_dialogues.get_dialogue(cfp_msg)
```


<br />