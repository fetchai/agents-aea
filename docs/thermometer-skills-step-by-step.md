This guide is a step-by-step introduction to building an AEA that represents static, and dynamic data to be advertised on the <a href=../oef-ledger>Open Economic Framework</a>.

If you simply want to run the resulting AEAs <a href="../thermometer-skills">go here</a>.

## Hardware Requirements (Optional)

To follow this tutorial to completion you will need:

 - Raspberry Pi 4
 
 - Mini SD card
 
 - Thermometer sensor
 
 - AEA Framework
	
The AEA will “live” inside the Raspberry Pi and will read the data from a sensor. Then it will connect to the [OEF search and communication node](../oef-ledger) and will identify itself as a seller of that data.

If you simply want to follow the software part of the guide then you only require the dependencies listed in the <a href="#dependencies">Dependencies</a> section.

### Setup the environment

You can follow the guide <a href=../raspberry-set-up> here </a> in order to setup your environment and prepare your Raspberry Pi.

Once you setup your Raspberry Pi, open a terminal and navigate to `/etc/udev/rules.d/`. Create a new file there  (I named mine `99-hidraw-permissions.rules`)
``` bash
sudo nano 99-hidraw-permissions.rules
```  
and add the following inside the file:
``` bash
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0664", GROUP="plugdev"
```
this assigns all devices coming out of the hidraw subsystem in the kernel to the group `plugdev` and sets the permissions to `r/w r/w r` (for root [the default owner], plugdev, and everyone else respectively).

## Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Thermometer AEA

### Step 1: Create the AEA

Create a new AEA by typing the following command in the terminal: 
``` bash
aea create my_thermometer
cd my_thermometer
```
Our newly created AEA is inside the current working directory. Let’s create our new skill that will handle the sale of the thermomemeter data. Type the following command:
``` bash
aea scaffold skill thermometer
```

This command will create the correct structure for a new skill inside our AEA project You can locate the newly created skill inside the skills folder (`my_thermometer/skills/thermometer/`) and it must contain the following files:

- `behaviours.py`
- `handlers.py`
- `my_model.py`
- `skills.yaml`
- `__init__.py`

### Step 2: Create the behaviour

A <a href="../api/skills/base#behaviour-objects">`Behaviour`</a> class contains the business logic specific to actions initiated by the AEA rather than reactions to other events.

Open the `behaviours.py` file (`my_thermometer/skills/thermometer/behaviours.py`) and add the following code:

``` python
from typing import Optional, cast

from aea.helpers.search.models import Description
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.thermometer.strategy import Strategy

DEFAULT_SERVICES_INTERVAL = 30.0


class ServiceRegistrationBehaviour(TickerBehaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        services_interval = kwargs.pop(
            "services_interval", DEFAULT_SERVICES_INTERVAL
        )  # type: int
        super().__init__(tick_interval=services_interval, **kwargs)
        self._registered_service_description = None  # type: Optional[Description]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if self.context.ledger_apis.has_ledger(strategy.ledger_id):
            balance = self.context.ledger_apis.token_balance(
                strategy.ledger_id,
                cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
            )
            if balance > 0:
                self.context.logger.info(
                    "[{}]: starting balance on {} ledger={}.".format(
                        self.context.agent_name, strategy.ledger_id, balance
                    )
                )
            else:
                self.context.logger.warning(
                    "[{}]: you have no starting balance on {} ledger!".format(
                        self.context.agent_name, strategy.ledger_id
                    )
                )

        self._register_service()

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        self._unregister_service()
        self._register_service()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if self.context.ledger_apis.has_ledger(strategy.ledger_id):
            balance = self.context.ledger_apis.token_balance(
                strategy.ledger_id,
                cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
            )
            self.context.logger.info(
                "[{}]: ending balance on {} ledger={}.".format(
                    self.context.agent_name, strategy.ledger_id, balance
                )
            )

        self._unregister_service()

    def _register_service(self) -> None:
        """
        Register to the OEF Service Directory.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        desc = strategy.get_service_description()
        self._registered_service_description = desc
        oef_msg_id = strategy.get_next_oef_msg_id()
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=(str(oef_msg_id), ""),
            service_description=desc,
        )
        msg.counterparty = self.context.search_service_address
        self.context.outbox.put_message(message=msg)
        self.context.logger.info(
            "[{}]: updating thermometer services on OEF service directory.".format(
                self.context.agent_name
            )
        )

    def _unregister_service(self) -> None:
        """
        Unregister service from OEF Service Directory.

        :return: None
        """
        if self._registered_service_description is not None:
            strategy = cast(Strategy, self.context.strategy)
            oef_msg_id = strategy.get_next_oef_msg_id()
            msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
                dialogue_reference=(str(oef_msg_id), ""),
                service_description=self._registered_service_description,
            )
            msg.counterparty = self.context.search_service_address
            self.context.outbox.put_message(message=msg)
            self.context.logger.info(
                "[{}]: unregistering thermometer station services from OEF service directory.".format(
                    self.context.agent_name
                )
            )
            self._registered_service_description = None
```

This <a href="../api/skills/behaviours#tickerbehaviour-objects">`TickerBehaviour`</a> registers and de-register our AEA’s service on the [OEF search node](../oef-ledger) at regular tick intervals (here 30 seconds). By registering, the AEA becomes discoverable to possible clients.

The act method unregisters and registers the AEA to the [OEF search node](../oef-ledger) on each tick. Finally, the teardown method unregisters the AEA and reports your balances.

At setup we are checking if we have a positive account balance for the AEA's address on the configured ledger.

### Step 3: Create the handler

So far, we have tasked the AEA with sending register/unregister requests to the [OEF search node](../oef-ledger). However, we have at present no way of handling the responses sent to the AEA by the [OEF search node](../oef-ledger) or messages sent from any other AEA.

We have to specify the logic to negotiate with another AEA based on the strategy we want our AEA to follow. The following diagram illustrates the negotiation flow, up to the agreement between a seller_AEA and a client_AEA.

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Client_AEA
        participant Seller_AEA
        participant Blockchain
    
        activate Client_AEA
        activate Search
        activate Seller_AEA
        activate Blockchain
        
        Seller_AEA->>Search: register_service
        Client_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Client_AEA->>Seller_AEA: call_for_proposal
        Seller_AEA->>Client_AEA: propose
        Client_AEA->>Seller_AEA: accept
        Seller_AEA->>Client_AEA: match_accept
        Client_AEA->>Blockchain: transfer_funds
        Client_AEA->>Seller_AEA: send_transaction_hash
        Seller_AEA->>Blockchain: check_transaction_status
        Seller_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Seller_AEA
        deactivate Blockchain
       
</div>

In the context of our thermometer use-case, the `my_thermometer` AEA is the seller.

Let us now implement a <a href="../api/skills/base#handler-objects">`Handler`</a> to deal with the incoming messages. Open the `handlers.py` file (`my_thermometer/skills/thermometer/handlers.py`) and add the following code:

``` python
import time
from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.helpers.search.models import Description, Query
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.skills.thermometer.dialogues import Dialogue, Dialogues
from packages.fetchai.skills.thermometer.strategy import Strategy


class FIPAHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        fipa_msg = cast(FipaMessage, message)

        # recover dialogue
        dialogues = cast(Dialogues, self.context.dialogues)
        fipa_dialogue = cast(Dialogue, dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FipaMessage.Performative.CFP:
            self._handle_cfp(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.ACCEPT:
            self._handle_accept(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, fipa_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
```
The code above is logic for handling `FipaMessages` received by the `my_thermometer` AEA. We use `Dialogues` (more on this below in <a href="#step-5-create-the-dialogues">this</a> section) to keep track of the dialogue state between the `my_thermometer` and the `client_aea`.

First, we check if the message is registered to an existing dialogue or if we have to create a new dialogue. The second part matches messages with their handler based on the message's performative. We are going to implement each case in a different function.

Below the unused `teardown` function, we continue by adding the following code:

``` python
    def _handle_unidentified_dialogue(self, msg: FipaMessage) -> None:
        """
        Handle an unidentified dialogue.

        Respond to the sender with a default message containing the appropriate error information.

        :param msg: the message

        :return: None
        """
        self.context.logger.info(
            "[{}]: unidentified dialogue.".format(self.context.agent_name)
        )
        default_msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": msg.encode()},
        )
        default_msg.counterparty = msg.counterparty
        self.context.outbox.put_message(message=default_msg)
```

The above code handles an unidentified dialogue by responding to the sender with a `DefaultMessage` containing the appropriate error information. 

The next code block handles the CFP message, paste the code below the `_handle_unidentified_dialogue` function:

``` python
    def _handle_cfp(self, msg: FipaMessage, dialogue: Dialogue) -> None:
        """
        Handle the CFP.

        If the CFP matches the supplied services then send a PROPOSE, otherwise send a DECLINE.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = msg.message_id + 1
        new_target = msg.message_id
        self.context.logger.info(
            "[{}]: received CFP from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        query = cast(Query, msg.query)
        strategy = cast(Strategy, self.context.strategy)

        if strategy.is_matching_supply(query):
            proposal, temp_data = strategy.generate_proposal_and_data(
                query, msg.counterparty
            )
            dialogue.temp_data = temp_data
            dialogue.proposal = proposal
            self.context.logger.info(
                "[{}]: sending a PROPOSE with proposal={} to sender={}".format(
                    self.context.agent_name, proposal.values, msg.counterparty[-5:]
                )
            )
            proposal_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FipaMessage.Performative.PROPOSE,
                proposal=proposal,
            )
            proposal_msg.counterparty = msg.counterparty
            dialogue.update(proposal_msg)
            self.context.outbox.put_message(message=proposal_msg)
        else:
            self.context.logger.info(
                "[{}]: declined the CFP from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
            decline_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FipaMessage.Performative.DECLINE,
            )
            decline_msg.counterparty = msg.counterparty
            dialogue.update(decline_msg)
            self.context.outbox.put_message(message=decline_msg)
```

The above code will respond with a `Proposal` to the client if the CFP matches the supplied services and our strategy otherwise it will respond with a `Decline` message. 

The next code-block  handles the decline message we receive from the client. Add the following code below the `_handle_cfp`function:

``` python 
    def _handle_decline(self, msg: FipaMessage, dialogue: Dialogue) -> None:
        """
        Handle the DECLINE.

        Close the dialogue.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received DECLINE from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        dialogues = cast(Dialogues, self.context.dialogues)
        dialogues.dialogue_stats.add_dialogue_endstate(
            Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated
        )
```
If we receive a decline message from the client we close the dialogue and terminate this conversation with the `client_aea`.

Alternatively, we might receive an `Accept` message. In order to handle this option add the following code below the `_handle_decline` function:

``` python
    def _handle_accept(self, msg: FipaMessage, dialogue: Dialogue) -> None:
        """
        Handle the ACCEPT.

        Respond with a MATCH_ACCEPT_W_INFORM which contains the address to send the funds to.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = msg.message_id + 1
        new_target = msg.message_id
        self.context.logger.info(
            "[{}]: received ACCEPT from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        self.context.logger.info(
            "[{}]: sending MATCH_ACCEPT_W_INFORM to sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        proposal = cast(Description, dialogue.proposal)
        identifier = cast(str, proposal.values.get("ledger_id"))
        match_accept_msg = FipaMessage(
            message_id=new_message_id,
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            target=new_target,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={"address": self.context.agent_addresses[identifier]},
        )
        match_accept_msg.counterparty = msg.counterparty
        dialogue.update(match_accept_msg)
        self.context.outbox.put_message(message=match_accept_msg)
```
When the `client_aea` accepts the `Proposal` we send it, and therefores sends us an `ACCEPT` message, we have to respond with another message (`MATCH_ACCEPT_W_INFORM` ) to inform the client about the address we would like it to send the funds to.

Lastly, we handle the `INFORM` message, which the client uses to inform us that it has sent the funds to the provided address. Add the following code:

``` python
    def _handle_inform(self, msg: FipaMessage, dialogue: Dialogue) -> None:
        """
        Handle the INFORM.

        If the INFORM message contains the transaction_digest then verify that it is settled, otherwise do nothing.
        If the transaction is settled, send the temperature data, otherwise do nothing.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = msg.message_id + 1
        new_target = msg.message_id
        self.context.logger.info(
            "[{}]: received INFORM from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )

        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_ledger_tx and ("transaction_digest" in msg.info.keys()):
            is_valid = False
            tx_digest = msg.info["transaction_digest"]
            self.context.logger.info(
                "[{}]: checking whether transaction={} has been received ...".format(
                    self.context.agent_name, tx_digest
                )
            )
            proposal = cast(Description, dialogue.proposal)
            ledger_id = cast(str, proposal.values.get("ledger_id"))
            not_settled = True
            time_elapsed = 0
            # TODO: fix blocking code; move into behaviour!
            while not_settled and time_elapsed < 60:
                is_valid = self.context.ledger_apis.is_tx_valid(
                    ledger_id,
                    tx_digest,
                    self.context.agent_addresses[ledger_id],
                    msg.counterparty,
                    cast(str, proposal.values.get("tx_nonce")),
                    cast(int, proposal.values.get("price")),
                )
                not_settled = not is_valid
                if not_settled:
                    time.sleep(2)
                    time_elapsed += 2
            # TODO: check the tx_digest references a transaction with the correct terms
            if is_valid:
                token_balance = self.context.ledger_apis.token_balance(
                    ledger_id, cast(str, self.context.agent_addresses.get(ledger_id))
                )
                self.context.logger.info(
                    "[{}]: transaction={} settled, new balance={}. Sending data to sender={}".format(
                        self.context.agent_name,
                        tx_digest,
                        token_balance,
                        msg.counterparty[-5:],
                    )
                )
                inform_msg = FipaMessage(
                    message_id=new_message_id,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=new_target,
                    performative=FipaMessage.Performative.INFORM,
                    info=dialogue.temp_data,
                )
                inform_msg.counterparty = msg.counterparty
                dialogue.update(inform_msg)
                self.context.outbox.put_message(message=inform_msg)
                dialogues = cast(Dialogues, self.context.dialogues)
                dialogues.dialogue_stats.add_dialogue_endstate(
                    Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
                )
            else:
                self.context.logger.info(
                    "[{}]: transaction={} not settled, aborting".format(
                        self.context.agent_name, tx_digest
                    )
                )
        elif "Done" in msg.info.keys():
            inform_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FipaMessage.Performative.INFORM,
                info=dialogue.temp_data,
            )
            inform_msg.counterparty = msg.counterparty
            dialogue.update(inform_msg)
            self.context.outbox.put_message(message=inform_msg)
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
            )
        else:
            self.context.logger.warning(
                "[{}]: did not receive transaction digest from sender={}.".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
```
We are checking the inform message. If it contains the transaction digest we verify that transaction matches the proposal that the client accepted. If the transaction is valid and we received the funds then we send the data to the client.  Otherwise we do not send the data.

### Step 4: Create the strategy

Next, we are going to create the strategy that we want our `my_thermometer` AEA to follow. Rename the `my_model.py` file (`my_thermometer/skills/thermometer/my_model.py`) to `strategy.py` and copy and paste the following code: 

``` python 
from random import randrange
from typing import Any, Dict, Tuple

from temper import Temper

from aea.helpers.search.models import Description, Query
from aea.mail.base import Address
from aea.skills.base import Model

from packages.fetchai.skills.thermometer.thermometer_data_model import (
    SCHEME,
    Thermometer_Datamodel,
)

DEFAULT_PRICE_PER_ROW = 1
DEFAULT_SELLER_TX_FEE = 0
DEFAULT_CURRENCY_PBK = "FET"
DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_IS_LEDGER_TX = True
DEFAULT_HAS_SENSOR = True


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._price_per_row = kwargs.pop("price_per_row", DEFAULT_PRICE_PER_ROW)
        self._seller_tx_fee = kwargs.pop("seller_tx_fee", DEFAULT_SELLER_TX_FEE)
        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_PBK)
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        self._has_sensor = kwargs.pop("has_sensor", DEFAULT_HAS_SENSOR)
        super().__init__(**kwargs)
        self._oef_msg_id = 0
```

We initialise the strategy class. We are trying to read the strategy variables from the yaml file. If this is not 
possible we specified some default values.

The following functions are related with 
the [OEF search node](../oef-ledger) registration and we assume that the query matches the supply. Add them under the initialization of the class:

``` python
    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    def get_next_oef_msg_id(self) -> int:
        """
        Get the next oef msg id.

        :return: the next oef msg id
        """
        self._oef_msg_id += 1
        return self._oef_msg_id

    def get_service_description(self) -> Description:
        """
        Get the service description.

        :return: a description of the offered services
        """
        desc = Description(SCHEME, data_model=Thermometer_Datamodel())
        return desc

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indiciating whether matches or not
        """
        # TODO, this is a stub
        return True

    def generate_proposal_and_data(
        self, query: Query, counterparty: Address
    ) -> Tuple[Description, Dict[str, Any]]:
        """
        Generate a proposal matching the query.

        :param counterparty: the counterparty of the proposal.
        :param query: the query
        :return: a tuple of proposal and the temprature data
        """
        if self.is_ledger_tx:
            tx_nonce = self.context.ledger_apis.generate_tx_nonce(
                identifier=self._ledger_id,
                seller=self.context.agent_addresses[self._ledger_id],
                client=counterparty,
            )
        else:
            tx_nonce = uuid.uuid4().hex
        temp_data = self._build_data_payload()
        total_price = self._price_per_row
        assert (
            total_price - self._seller_tx_fee > 0
        ), "This sale would generate a loss, change the configs!"
        proposal = Description(
            {
                "price": total_price,
                "seller_tx_fee": self._seller_tx_fee,
                "currency_id": self._currency_id,
                "ledger_id": self._ledger_id,
                "tx_nonce": tx_nonce,
            }
        )
        return proposal, temp_data

    def _build_data_payload(self) -> Dict[str, Any]:
        """
        Build the data payload.

        :return: a tuple of the data and the rows
        """
        if self._has_sensor:
            temper = Temper()
            while True:
                results = temper.read()
                if "internal temperature" in results[0].keys():
                    degrees = {"thermometer_data": str(results)}
                else:
                    self.context.logger.debug(
                        "Couldn't read the sensor I am re-trying."
                    )
        else:
            degrees = {"thermometer_data": str(randrange(10, 25))}  # nosec
            self.context.logger.info(degrees)

        return degrees
```

Before the creation of the actual proposal, we have to check if the sale generates value for us or a loss. If it is a loss, we abort and warn the developer. The helper private function `_build_data_payload`, is where we read data from our sensor or in case we do not have a sensor generate a random number.

### Step 5: Create the dialogues

When we are negotiating with other AEAs we would like to keep track of the state of these negotiations. To this end we create a new file in the skill folder (`my_thermometer/skills/thermometer/`) and name it `dialogues.py`. Inside this file add the following code: 

``` python
from typing import Dict, Optional

from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.helpers.search.models import Description
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.skills.base import Model

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues


class Dialogue(FipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
        agent_address: Address,
        role: BaseDialogue.Role,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        FipaDialogue.__init__(
            self, dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )
        self.temp_data = None  # type: Optional[Dict[str, str]]
        self.proposal = None  # type: Optional[Description]


class Dialogues(Model, FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        FipaDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """
        Infer the role of the agent from an incoming or outgoing first message

        :param message: an incoming/outgoing first message
        :return: the agent's role
        """
        return FipaDialogue.AgentRole.SELLER

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> Dialogue:
        """
        Create an instance of dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = Dialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue
```

The `Dialogues` class stores dialogue with each `client_aea` (and other AEAs) and exposes a number of helpful methods to manage them. This helps us match messages to a dialogue, access previous messages and enable us to identify possible communications problems between the `my_thermometer` AEA and the `my_client` AEA. It also keeps track of the data that we offer for sale during the proposal phase.

The `Dialogues` class extends `FipaDialogues`, which itself derives from the base <a href="../api/helpers/dialogue/base#dialogues-objects">`Dialogues`</a> class. Similarly, the `Dialogue` class extends `FipaDialogue`, which itself derives from the base <a href="../api/helpers/dialogue/base#dialogue-objects">`Dialogue`</a> class. To learn more about dialogues have a look <a href="../protocol">here</a>.

### Step 6: Create the data_model

Each AEA in the oef needs a <a href="../api/helpers/search/models#description-objects">`Description`</a> in order to be able to register as a service. The <a href="../api/helpers/search/models#datamodel-objects">`DataModel`</a> will help us create this description. Create a new file in the skill directory (`my_thermometer/skills/thermometer/`) and call it `thermometer_data_model.py` and paste the following code: 

``` python
from aea.helpers.search.models import Attribute, DataModel

SCHEME = {"country": "UK", "city": "Cambridge"}


class Thermometer_Datamodel(DataModel):
    """Data model for the thermo Agent."""

    def __init__(self):
        """Initialise the dataModel."""
        self.attribute_country = Attribute("country", str, True)
        self.attribute_city = Attribute("city", str, True)

        super().__init__(
            "thermometer_datamodel", [self.attribute_country, self.attribute_city]
        )
```

This data model registers to the [OEF search node](../oef-ledger) as an AEA that is in the UK and specifically in Cambridge. If a `client_AEA` searches for AEA in the UK the [OEF search node](../oef-ledger) will respond with the address of our AEA.

### Step 7: Update the YAML files

Since we made so many changes to our AEA we have to update the `skill.yaml` (at `my_thermometer/skills/thermometer/skill.yaml`). Make sure that your `skill.yaml` matches with the following code 

``` yaml
name: thermometer
author: fetchai
version: 0.2.0
license: Apache-2.0
fingerprint: {}
aea_version: '>=0.4.0, <0.5.0'
description: "The thermometer skill implements the functionality to sell data."
behaviours:
  service_registration:
    class_name: ServiceRegistrationBehaviour
    args:
      services_interval: 60
handlers:
  fipa:
    class_name: FIPAHandler
    args: {}
models:
  strategy:
    class_name: Strategy
    args:
      price_per_row: 1
      seller_tx_fee: 0
      currency_id: 'FET'
      ledger_id: 'fetchai'
      has_sensor: True
      is_ledger_tx: True
  dialogues:
    class_name: Dialogues
    args: {}
protocols: ['fetchai/fipa:0.3.0', 'fetchai/oef_search:0.2.0', 'fetchai/default:0.2.0']
ledgers: ['fetchai']
dependencies:
  pyserial: {}
  temper-py: {}
```

We must pay attention to the models and in particular the strategy’s variables. Here we can change the price we would like to sell each reading for or the currency we would like to transact with. Lastly, the dependencies are the third party packages we need to install in order to get readings from the sensor. 

Finally, we fingerprint our new skill:

``` bash
aea fingerprint skill thermometer
```

This will hash each file and save the hash in the fingerprint. This way, in the future we can easily track if any of the files have changed.


## Client_AEA

### Step 1: Create the AEA

Create a new AEA by typing the following command in the terminal:

``` bash
aea create my_client
cd my_client
```

Our newly created AEA is inside the current working directory. Let’s create our new skill that will handle the purchase of the thermometer data. Type the following command:

``` bash
aea scaffold skill thermometer_client
```

This command will create the correct structure for a new skill inside our AEA project You can locate the newly created skill inside the skills folder (`my_client/skills/thermometer_client/`) and it must contain the following files:

- `behaviours.py`
- `handlers.py`
- `my_model.py`
- `skills.yaml`
- `__init__.py`

### Step 2: Create the behaviour

A <a href="../api/skills/base#behaviour-objects">`Behaviour`</a> class contains the business logic specific to actions initiated by the AEA rather than reactions to other events.

Open the `behaviours.py` (`my_client/skills/thermometer_client/behaviours.py`) and add the following code:

``` python 
from typing import cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.thermometer_client.strategy import Strategy

DEFAULT_SEARCH_INTERVAL = 5.0


class MySearchBehaviour(TickerBehaviour):
    """This class implements a search behaviour."""

    def __init__(self, **kwargs):
        """Initialize the search behaviour."""
        search_interval = cast(
            float, kwargs.pop("search_interval", DEFAULT_SEARCH_INTERVAL)
        )
        super().__init__(tick_interval=search_interval, **kwargs)

    def setup(self) -> None:
        """Implement the setup for the behaviour."""
        strategy = cast(Strategy, self.context.strategy)
        if self.context.ledger_apis.has_ledger(strategy.ledger_id):
            balance = self.context.ledger_apis.token_balance(
                strategy.ledger_id,
                cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
            )
            if balance > 0:
                self.context.logger.info(
                    "[{}]: starting balance on {} ledger={}.".format(
                        self.context.agent_name, strategy.ledger_id, balance
                    )
                )
            else:
                self.context.logger.warning(
                    "[{}]: you have no starting balance on {} ledger!".format(
                        self.context.agent_name, strategy.ledger_id
                    )
                )
                self.context.is_active = False

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_searching:
            query = strategy.get_service_query()
            search_id = strategy.get_next_search_id()
            oef_msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=(str(search_id), ""),
                query=query,
            )
            oef_msg.counterparty = self.context.search_service_address
            self.context.outbox.put_message(message=oef_msg)

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if self.context.ledger_apis.has_ledger(strategy.ledger_id):
            balance = self.context.ledger_apis.token_balance(
                strategy.ledger_id,
                cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
            )
            self.context.logger.info(
                "[{}]: ending balance on {} ledger={}.".format(
                    self.context.agent_name, strategy.ledger_id, balance
                )
            )
```

This <a href="../api/skills/behaviours#tickerbehaviour-objects">`TickerBehaviour`</a> will search on  the[OEF search node](../oef-ledger) with a specific query at regular tick intervals. 

### Step 3: Create the handler

So far, we have tasked the AEA with sending search queries to the [OEF search node](../oef-ledger). However, we have at present no way of handling the responses sent to the AEA by the [OEF search node](../oef-ledger) or messages sent by other agent.

Let us now implement a <a href="../api/skills/base#handler-objects">`Handler`</a> to deal with the incoming messages. Open the `handlers.py` file (`my_client/skills/thermometer_client/handlers.py`) and add the following code:

``` python
import pprint
from typing import Any, Dict, Optional, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Description
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.thermometer_client.dialogues import Dialogue, Dialogues
from packages.fetchai.skills.thermometer_client.strategy import Strategy


class FIPAHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        fipa_msg = cast(FipaMessage, message)

        # recover dialogue
        dialogues = cast(Dialogues, self.context.dialogues)
        fipa_dialogue = cast(Dialogue, dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FipaMessage.Performative.PROPOSE:
            self._handle_propose(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.MATCH_ACCEPT_W_INFORM:
            self._handle_match_accept(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, fipa_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
```
You will see that we are following similar logic to the thermometer when we develop the client’s side of the negotiation. First, we create a new dialogue and we store it in the dialogues class. Then we are checking what kind of message we received. So lets start creating our handlers:

``` python 
    def _handle_unidentified_dialogue(self, msg: FipaMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: unidentified dialogue.".format(self.context.agent_name)
        )
        default_msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": msg.encode()},
        )
        default_msg.counterparty = msg.counterparty
        self.context.outbox.put_message(message=default_msg)
```
The above code handles the unidentified dialogues. And responds with an error message to the sender. Next we will handle the `Proposal` that we receive from the `my_thermometer` AEA: 

``` python
    def _handle_propose(self, msg: FipaMessage, dialogue: Dialogue) -> None:
        """
        Handle the propose.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = msg.message_id + 1
        new_target = msg.message_id
        proposal = msg.proposal
        self.context.logger.info(
            "[{}]: received proposal={} from sender={}".format(
                self.context.agent_name, proposal.values, msg.counterparty[-5:]
            )
        )
        strategy = cast(Strategy, self.context.strategy)
        acceptable = strategy.is_acceptable_proposal(proposal)
        affordable = strategy.is_affordable_proposal(proposal)
        if acceptable and affordable:
            strategy.is_searching = False
            self.context.logger.info(
                "[{}]: accepting the proposal from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
            dialogue.proposal = proposal
            accept_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FipaMessage.Performative.ACCEPT,
            )
            accept_msg.counterparty = msg.counterparty
            dialogue.update(accept_msg)
            self.context.outbox.put_message(message=accept_msg)
        else:
            self.context.logger.info(
                "[{}]: declining the proposal from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
            decline_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FipaMessage.Performative.DECLINE,
            )
            decline_msg.counterparty = msg.counterparty
            dialogue.update(decline_msg)
            self.context.outbox.put_message(message=decline_msg)
```
When we receive a proposal we have to check if we have the funds to complete the transaction and if the proposal is acceptable based on our strategy. If the proposal is not affordable or acceptable we respond with a `DECLINE` message. Otherwise, we send an `ACCEPT` message to the seller.

The next code-block handles the `DECLINE` message that we may receive from the client on our `CFP`message or our `ACCEPT` message:

``` python
    def _handle_decline(self, msg: FipaMessage, dialogue: Dialogue) -> None:
        """
        Handle the decline.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received DECLINE from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        target = msg.get("target")
        dialogues = cast(Dialogues, self.context.dialogues)
        if target == 1:
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated
            )
        elif target == 3:
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated
            )
```
The above code terminates each dialogue with the specific AEA and stores the step. For example, if the `target == 1` we know that the seller declined our `CFP` message.

In case we do not receive any `DECLINE` message that means that the `my_thermometer` AEA want to move on with the sale, in that case, it will send a `MATCH_ACCEPT` message. In order to handle this we add the following code: 

``` python
    def _handle_match_accept(self, msg: FipaMessage, dialogue: Dialogue) -> None:
        """
        Handle the match accept.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_ledger_tx:
            self.context.logger.info(
                "[{}]: received MATCH_ACCEPT_W_INFORM from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
            info = msg.info
            address = cast(str, info.get("address"))
            proposal = cast(Description, dialogue.proposal)
            tx_msg = TransactionMessage(
                performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
                skill_callback_ids=[self.context.skill_id],
                tx_id="transaction0",
                tx_sender_addr=self.context.agent_addresses[
                    proposal.values["ledger_id"]
                ],
                tx_counterparty_addr=address,
                tx_amount_by_currency_id={
                    proposal.values["currency_id"]: -proposal.values["price"]
                },
                tx_sender_fee=strategy.max_buyer_tx_fee,
                tx_counterparty_fee=proposal.values["seller_tx_fee"],
                tx_quantities_by_good_id={},
                ledger_id=proposal.values["ledger_id"],
                info={"dialogue_label": dialogue.dialogue_label.json},
                tx_nonce=proposal.values["tx_nonce"],
            )
            self.context.decision_maker_message_queue.put_nowait(tx_msg)
            self.context.logger.info(
                "[{}]: proposing the transaction to the decision maker. Waiting for confirmation ...".format(
                    self.context.agent_name
                )
            )
        else:
            new_message_id = msg.message_id + 1
            new_target = msg.message_id
            inform_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FipaMessage.Performative.INFORM,
                info={"Done": "Sending payment via bank transfer"},
            )
            inform_msg.counterparty = msg.counterparty
            dialogue.update(inform_msg)
            self.context.outbox.put_message(message=inform_msg)
            self.context.logger.info(
                "[{}]: informing counterparty={} of payment.".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
```
The first thing we are checking is if we enabled our AEA to transact with a ledger. If we can transact with a ledger we generate a transaction message and we propose it to the `DecisionMaker` (more on the `DecisionMaker` <a href="../decision-maker">here</a>. The `DecisionMaker` then will check the transaction message. If it is acceptable (i.e. we have the funds, etc) it signs and sends the transaction to the specified ledger. Then it returns us the transaction digest.

Lastly, we need to handle the `INFORM` message. This is the message that will have our data:

``` python
    def _handle_inform(self, msg: FipaMessage, dialogue: Dialogue) -> None:
        """
        Handle the match inform.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received INFORM from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        if "thermometer_data" in msg.info.keys():
            thermometer_data = msg.info["thermometer_data"]
            self.context.logger.info(
                "[{}]: received the following thermometer data={}".format(
                    self.context.agent_name, pprint.pformat(thermometer_data)
                )
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
            )
        else:
            self.context.logger.info(
                "[{}]: received no data from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
```
The main difference between the `thermometer_client` and the `thermometer` skill `handlers.py` file is that in this one we create more than one handler.

The reason is that we receive messages not only from the `my_thermometer` AEA but also from the `DecisionMaker` and the [OEF search node](../oef-ledger). We need one handler for each type of protocol we use.

To handle the messages in the `oef_search` protocol used by the [OEF search node](../oef-ledger) we add the following code in the same file (`my_client/skills/thermometer_client/handlers.py`):

``` python 
class OEFSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        # convenience representations
        oef_msg = cast(OefSearchMessage, message)
        if oef_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            agents = oef_msg.agents
            self._handle_search(agents)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_search(self, agents: Tuple[str, ...]) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :return: None
        """
        if len(agents) > 0:
            self.context.logger.info(
                "[{}]: found agents={}, stopping search.".format(
                    self.context.agent_name, list(map(lambda x: x[-5:], agents))
                )
            )
            strategy = cast(Strategy, self.context.strategy)
            # stopping search
            strategy.is_searching = False
            # pick first agent found
            opponent_addr = agents[0]
            dialogues = cast(Dialogues, self.context.dialogues)
            query = strategy.get_service_query()
            self.context.logger.info(
                "[{}]: sending CFP to agent={}".format(
                    self.context.agent_name, opponent_addr[-5:]
                )
            )
            cfp_msg = FipaMessage(
                message_id=Dialogue.STARTING_MESSAGE_ID,
                dialogue_reference=dialogues.new_self_initiated_dialogue_reference(),
                performative=FipaMessage.Performative.CFP,
                target=Dialogue.STARTING_TARGET,
                query=query,
            )
            cfp_msg.counterparty = opponent_addr
            dialogues.update(cfp_msg)
            self.context.outbox.put_message(message=cfp_msg)
        else:
            self.context.logger.info(
                "[{}]: found no agents, continue searching.".format(
                    self.context.agent_name
                )
            )
```
When we receive a message from the [OEF search node](../oef-ledger) of a type `OefSearchMessage.Performative.SEARCH_RESULT`, we are passing the details to the relevant handler method. In the `_handle_search` function we are checking that the response contains some agents and we stop the search if it does. We pick our first agent and we send a `CFP` message.

The last handler we need is the `MyTransactionHandler`. This handler will handle the internal messages that we receive from the `DecisionMaker`.

``` python 
class MyTransactionHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = TransactionMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        tx_msg_response = cast(TransactionMessage, message)
        if (
            tx_msg_response is not None
            and tx_msg_response.performative
            == TransactionMessage.Performative.SUCCESSFUL_SETTLEMENT
        ):
            self.context.logger.info(
                "[{}]: transaction was successful.".format(self.context.agent_name)
            )
            json_data = {"transaction_digest": tx_msg_response.tx_digest}
            info = cast(Dict[str, Any], tx_msg_response.info)
            dialogue_label = DialogueLabel.from_json(
                cast(Dict[str, str], info.get("dialogue_label"))
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogue = dialogues.dialogues[dialogue_label]
            fipa_msg = cast(FipaMessage, dialogue.last_incoming_message)
            new_message_id = fipa_msg.message_id + 1
            new_target_id = fipa_msg.message_id
            counterparty_addr = dialogue.dialogue_label.dialogue_opponent_addr
            inform_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target_id,
                performative=FipaMessage.Performative.INFORM,
                info=json_data,
            )
            inform_msg.counterparty = counterparty_addr
            dialogue.update(inform_msg)
            self.context.outbox.put_message(message=inform_msg)
            self.context.logger.info(
                "[{}]: informing counterparty={} of transaction digest.".format(
                    self.context.agent_name, counterparty_addr[-5:]
                )
            )
        else:
            self.context.logger.info(
                "[{}]: transaction was not successful.".format(self.context.agent_name)
            )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
```
Remember that we send a message to the `DecisionMaker` with a transaction proposal. Here, we handle the response from the `DecisionMaker`.

If the message is of performative `SUCCESFUL_SETTLEMENT`, we generate the `INFORM` message for the `thermometer` to inform it that we completed the transaction and transferred the funds to the address that it sent us. We also pass along the transaction digest so the `thermometer` aea can verify the transaction.

If the transaction was unsuccessful, the `DecisionMaker` will inform us that something went wrong and the transaction was not successful.

### Step 4: Create the strategy

We are going to create the strategy that we want our AEA to follow. Rename the `my_model.py` file (in `my_client/skills/thermometer_client/`) to `strategy.py` and paste the following code: 

``` python
from typing import cast

from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.skills.base import Model

DEFAULT_COUNTRY = "UK"
SEARCH_TERM = "country"
DEFAULT_MAX_ROW_PRICE = 5
DEFAULT_MAX_TX_FEE = 20000000
DEFAULT_CURRENCY_PBK = "ETH"
DEFAULT_LEDGER_ID = "ethereum"
DEFAULT_IS_LEDGER_TX = True


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._country = kwargs.pop("country", DEFAULT_COUNTRY)
        self._max_row_price = kwargs.pop("max_row_price", DEFAULT_MAX_ROW_PRICE)
        self.max_buyer_tx_fee = kwargs.pop("max_tx_fee", DEFAULT_MAX_TX_FEE)
        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_PBK)
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        super().__init__(**kwargs)
        self._search_id = 0
        self.is_searching = True
```

We initialize the strategy class by trying to read the strategy variables from the YAML file. If this is not possible we specified some default values. The following two functions are related to the oef search service, add them under the initialization of the class:

``` python
    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    def get_next_search_id(self) -> int:
        """
        Get the next search id and set the search time.

        :return: the next search id
        """
        self._search_id += 1
        return self._search_id

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        query = Query(
            [Constraint(SEARCH_TERM, ConstraintType("==", self._country))], model=None
        )
        return query
```

The following code block checks if the proposal that we received is acceptable based on the strategy:

``` python 
    def is_acceptable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an acceptable proposal.

        :return: whether it is acceptable
        """
        result = (
            (proposal.values["price"] - proposal.values["seller_tx_fee"] > 0)
            and (proposal.values["price"] <= self._max_row_price)
            and (proposal.values["currency_id"] == self._currency_id)
            and (proposal.values["ledger_id"] == self._ledger_id)
        )
        return result
```

The `is_affordable_proposal` method checks if we can afford the transaction based on the funds we have in our wallet on the ledger.

``` python 
    def is_affordable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an affordable proposal.

        :return: whether it is affordable
        """
        if self.is_ledger_tx:
            payable = proposal.values["price"] + self.max_buyer_tx_fee
            ledger_id = proposal.values["ledger_id"]
            address = cast(str, self.context.agent_addresses.get(ledger_id))
            balance = self.context.ledger_apis.token_balance(ledger_id, address)
            result = balance >= payable
        else:
            result = True
        return result
```

### Step 5: Create the dialogues

As mentioned, when we are negotiating with other AEA we would like to keep track of these negotiations for various reasons. Create a new file and name it `dialogues.py` (in `my_client/skills/thermometer_client/`). Inside this file add the following code: 

``` python
from typing import Optional

from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.helpers.search.models import Description
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.skills.base import Model

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues


class Dialogue(FipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
        agent_address: Address,
        role: BaseDialogue.Role,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        FipaDialogue.__init__(
            self, dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )
        self.proposal = None  # type: Optional[Description]


class Dialogues(Model, FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        FipaDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """
        Infer the role of the agent from an incoming or outgoing first message

        :param message: an incoming/outgoing first message
        :return: the agent's role
        """
        return FipaDialogue.AgentRole.BUYER

    def _create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> Dialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = Dialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue
```

The dialogues class stores dialogue with each AEA so we can have access to previous messages and enable us to identify possible communications problems between the `my_thermometer` AEA and the `my_client` AEA.

### Step 6: Update the YAML files

Since we made so many changes to our AEA we have to update the `skill.yaml` to contain our newly created scripts and the details that will be used from the strategy.

First, we update the `skill.yaml`. Make sure that your `skill.yaml` matches with the following code:

``` yaml
name: thermometer_client
author: fetchai
version: 0.1.0
license: Apache-2.0
fingerprint: {}
aea_version: '>=0.4.0, <0.5.0'
description: "The thermometer client skill implements the skill to purchase temperature data."
behaviours:
  search:
    class_name: MySearchBehaviour
    args:
      search_interval: 5
handlers:
  fipa:
    class_name: FIPAHandler
    args: {}
  oef:
    class_name: OEFHandler
    args: {}
  transaction:
    class_name: MyTransactionHandler
    args: {}
models:
  strategy:
    class_name: Strategy
    args:
      country: UK
      max_row_price: 4
      max_tx_fee: 2000000
      currency_id: 'FET'
      ledger_id: 'fetchai'
      is_ledger_tx: True
  dialogues:
    class_name: Dialogues
    args: {}
protocols: ['fetchai/fipa:0.3.0','fetchai/default:0.2.0','fetchai/oef_search:0.2.0']
ledgers: ['fetchai']
```
We must pay attention to the models and the strategy’s variables. Here we can change the price we would like to buy each reading at or the currency we would like to transact with. 

Finally, we fingerprint our new skill:

``` bash
aea fingerprint skill thermometer
```

This will hash each file and save the hash in the fingerprint. This way, in the future we can easily track if any of the files have changed.

## Run the AEAs

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>If you are using the Raspberry Pi, make sure that your thermometer sensor is connected to the Raspberry Pi's USB port.</p>
</div>

You can change the end-point's address and port by modifying the connection's yaml file (`*vendor/fetchai/connections/oef/connection.yaml`)

Under config locate:

``` yaml
addr: ${OEF_ADDR: 127.0.0.1}
```
and replace it with your IP (the IP of the machine that runs the [OEF search and communication node](../oef-ledger) image.)

In a separate terminal, launch a local [OEF search and communication node](../oef-ledger).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

### Fetch.ai ledger payment

Create the private key for the weather client AEA.

``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

#### Update the AEA configs

Both in `my_thermometer/aea-config.yaml` and `my_client/aea-config.yaml`, replace ```ledger_apis```: {} with the following.
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
#### Fund the temperature client AEA

Create some wealth for your weather client on the Fetch.ai testnet. (It takes a while).

``` bash 
aea generate-wealth fetchai
```

#### Run both AEAs

Run both AEAs from their respective terminals

``` bash 
aea add connection fetchai/oef:0.4.0
aea install
aea config set agent.default_connection fetchai/oef:0.4.0
aea run --connections fetchai/oef:0.4.0
```
You will see that the AEAs negotiate and then transact using the Fetch.ai testnet.

### Ethereum ledger payment

A demo to run the same scenario but with a true ledger transaction on the Ethereum Ropsten testnet. 
This demo assumes the temperature client trusts our AEA to send the temperature data upon successful payment.

Create the private key for the `my_client` AEA.

``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

#### Update the AEA configs

Both in `my_thermometer/aea-config.yaml` and `my_client/aea-config.yaml`, replace `ledger_apis: {}` with the following.

``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

#### Update the skill configs

In the thermometer skill config (`my_thermometer/skills/thermometer/skill.yaml`) under strategy, amend the `currency_id` and `ledger_id` as follows.

``` yaml
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
```

In the `temprature_client` skill config (`my_client/skills/temprature_client/skill.yaml`) under strategy change the `currency_id` and `ledger_id`.

``` yaml
max_buyer_tx_fee: 20000
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
```

#### Fund the thermometer client AEA

Create some wealth for your weather client on the Ethereum Ropsten test net.
Go to the <a href="https://faucet.metamask.io/"> MetaMask Faucet </a> and request some test ETH for the account your weather client AEA is using (you need to first load your AEAs private key into MetaMask). Your private key is at `my_client/eth_private_key.txt`.

#### Run both AEAs

Run both AEAs from their respective terminals.

``` bash 
aea add connection fetchai/oef:0.4.0
aea install
aea config set agent.default_connection fetchai/oef:0.4.0
aea run --connections fetchai/oef:0.4.0
```

You will see that the AEAs negotiate and then transact using the Ethereum testnet.

## Delete the AEAs

When you are done, go up a level and delete the AEAs.
``` bash 
cd ..
aea delete my_thermometer
aea delete my_client
```

## Next steps

You have completed the "Getting Started" series. Congratulations!

### Recommended

We recommend you build your own AEA next. There are many helpful guides on here and a developer community on <a href="fetch-ai.slack.com">Slack</a>. Speak to you there!

<br />
