This guide is a step-by-step introduction to building an AEA that represents static, and dynamic data to be advertised on the <a href=../oef-ledger>Open Economic Framework</a>.

If you simply want to run the resulting AEAs <a href="../generic-skills">go here</a>.

<!-- ## Hardware Requirements (Optional)

To follow this tutorial to completion you will need:

 - Raspberry Pi 4
 
 - Mini SD card
 
 - Thermometer sensor
 
 - AEA Framework
	
The AEA will “live” inside the Raspberry Pi and will read the data from a sensor. Then it will connect to the [OEF search and communication node](../oef-ledger) and will identify itself as a seller of that data.

If you simply want to follow the software part of the guide then you only require the dependencies listed in the <a href="#dependencies">Dependencies</a> section.

### Setup the environment (Optional)

You can follow the guide <a href=../raspberry-set-up> here </a> in order to setup your environment and prepare your Raspberry Pi.

Once you setup your Raspberry Pi, open a terminal and navigate to `/etc/udev/rules.d/`. Create a new file there  (I named mine `99-hidraw-permissions.rules`)
``` bash
sudo nano 99-hidraw-permissions.rules
```  
and add the following inside the file:
``` bash
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0664", GROUP="plugdev"
```
this assigns all devices coming out of the hidraw subsystem in the kernel to the group `plugdev` and sets the permissions to `r/w r/w r` (for root [the default owner], plugdev, and everyone else respectively). -->

## Dependencies (Required)

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Reference (Optional)

This step-by-step guide recreates two AEAs already developed by Fetch.ai. You can get the finished AEAs to compare your code against by following the next steps:

``` bash
aea fetch fetchai/generic_seller:0.3.0
cd generic_seller
aea eject skill fetchai/generic_seller:0.6.0
cd ..
```

``` bash
aea fetch fetchai/generic_buyer:0.3.0
cd generic_buyer
aea eject skill fetchai/generic_buyer:0.5.0
cd ..
```

## Generic Seller AEA

### Step 1: Create the AEA

Create a new AEA by typing the following command in the terminal: 
``` bash
aea create my_generic_seller
cd my_generic_seller
```
Our newly created AEA is inside the current working directory. Let’s create our new skill that will handle the sale of data. Type the following command:
``` bash
aea scaffold skill generic_seller
```

This command will create the correct structure for a new skill inside our AEA project You can locate the newly created skill inside the skills folder (`my_generic_seller/skills/generic_seller/`) and it must contain the following files:

- `behaviours.py`
- `handlers.py`
- `my_model.py`
- `skills.yaml`
- `__init__.py`

### Step 2: Create the behaviour

A <a href="../api/skills/base#behaviour-objects">`Behaviour`</a> class contains the business logic specific to actions initiated by the AEA rather than reactions to other events.

Open the `behaviours.py` file (`my_generic_seller/skills/generic_seller/behaviours.py`) and add the following code:

``` python
from typing import Optional, cast

from aea.helpers.search.models import Description
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_seller.dialogues import (
    LedgerApiDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.generic_seller.strategy import GenericStrategy


DEFAULT_SERVICES_INTERVAL = 30.0
LEDGER_API_ADDRESS = "fetchai/ledger:0.1.0"


class GenericServiceRegistrationBehaviour(TickerBehaviour):
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
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_ledger_tx:
            ledger_api_dialogues = cast(
                LedgerApiDialogues, self.context.ledger_api_dialogues
            )
            ledger_api_msg = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_BALANCE,
                dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
                ledger_id=strategy.ledger_id,
                address=cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
            )
            ledger_api_msg.counterparty = LEDGER_API_ADDRESS
            ledger_api_dialogues.update(ledger_api_msg)
            self.context.outbox.put_message(message=ledger_api_msg)
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
        self._unregister_service()

    def _register_service(self) -> None:
        """
        Register to the OEF Service Directory.

        :return: None
        """
        strategy = cast(GenericStrategy, self.context.strategy)
        description = strategy.get_service_description()
        self._registered_service_description = description
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=description,
        )
        oef_search_msg.counterparty = self.context.search_service_address
        oef_search_dialogues.update(oef_search_msg)
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info(
            "[{}]: updating services on OEF service directory.".format(
                self.context.agent_name
            )
        )

    def _unregister_service(self) -> None:
        """
        Unregister service from OEF Service Directory.

        :return: None
        """
        if self._registered_service_description is None:
            return
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=self._registered_service_description,
        )
        oef_search_msg.counterparty = self.context.search_service_address
        oef_search_dialogues.update(oef_search_msg)
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info(
            "[{}]: unregistering services from OEF service directory.".format(
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

We have to specify the logic to negotiate with another AEA based on the strategy we want our AEA to follow. The following diagram illustrates the negotiation flow, up to the agreement between a seller_AEA and a buyer_AEA.

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Buyer_AEA
        participant Seller_AEA
        participant Blockchain
    
        activate Buyer_AEA
        activate Search
        activate Seller_AEA
        activate Blockchain
        
        Seller_AEA->>Search: register_service
        Buyer_AEA->>Search: search
        Search-->>Buyer_AEA: list_of_agents
        Buyer_AEA->>Seller_AEA: call_for_proposal
        Seller_AEA->>Buyer_AEA: propose
        Buyer_AEA->>Seller_AEA: accept
        Seller_AEA->>Buyer_AEA: match_accept
        loop Once with LedgerConnection
            Buyer_AEA->>Buyer_AEA: Get raw transaction from ledger api
        end
        loop Once with DecisionMaker
            Buyer_AEA->>Buyer_AEA: Get signed transaction from decision maker
        end
        loop Once with LedgerConnection
            Buyer_AEA->>Buyer_AEA: Send transaction and get digest from ledger api
            Buyer_AEA->>Blockchain: transfer_funds
        end
        Buyer_AEA->>Seller_AEA: send_transaction_digest
        Seller_AEA->>Blockchain: check_transaction_status
        Seller_AEA->>Buyer_AEA: send_data
        
        deactivate Buyer_AEA
        deactivate Search
        deactivate Seller_AEA
        deactivate Blockchain
       
</div>

In the context of our generic use-case, the `my_generic_seller` AEA is the seller.

Let us now implement a <a href="../api/skills/base#handler-objects">`Handler`</a> to deal with the incoming messages. Open the `handlers.py` file (`my_generic_seller/skills/generic_seller/handlers.py`) and add the following code:

``` python
from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.transaction.base import TransactionDigest
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_seller.dialogues import (
    DefaultDialogues,
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.generic_seller.strategy import GenericStrategy

LEDGER_API_ADDRESS = "fetchai/ledger:0.1.0"


class GenericFipaHandler(Handler):
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
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        fipa_dialogue = cast(FipaDialogue, fipa_dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FipaMessage.Performative.CFP:
            self._handle_cfp(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, fipa_dialogue, fipa_dialogues)
        elif fipa_msg.performative == FipaMessage.Performative.ACCEPT:
            self._handle_accept(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, fipa_dialogue)
        else:
            self._handle_invalid(fipa_msg, fipa_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
```
The code above is logic for handling `FipaMessages` received by the `my_generic_seller` AEA. We use `FipaDialogues` (more on this below in <a href="#step-5-create-the-dialogues">this</a> section) to keep track of the dialogue state between the `my_generic_seller` AEA and the `my_generic_buyer` AEA.

First, we check if the message is registered to an existing dialogue or if we have to create a new dialogue. The second part matches messages with their handler based on the message's performative. We are going to implement each case in a different function.

Below the unused `teardown` function, we continue by adding the following code:

``` python
    def _handle_unidentified_dialogue(self, fipa_msg: FipaMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param fipa_msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid fipa message={}, unidentified dialogue.".format(
                self.context.agent_name, fipa_msg
            )
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg = DefaultMessage(
            performative=DefaultMessage.Performative.ERROR,
            dialogue_reference=default_dialogues.new_self_initiated_dialogue_reference(),
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": fipa_msg.encode()},
        )
        default_msg.counterparty = fipa_msg.counterparty
        default_dialogues.update(default_msg)
        self.context.outbox.put_message(message=default_msg)
```

The above code handles an unidentified dialogue by responding to the sender with a `DefaultMessage` containing the appropriate error information. 

The next code block handles the CFP message, paste the code below the `_handle_unidentified_dialogue` function:

``` python
    def _handle_cfp(self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue) -> None:
        """
        Handle the CFP.

        If the CFP matches the supplied services then send a PROPOSE, otherwise send a DECLINE.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received CFP from sender={}".format(
                self.context.agent_name, fipa_msg.counterparty[-5:]
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_matching_supply(fipa_msg.query):
            proposal, terms, data_for_sale = strategy.generate_proposal_terms_and_data(
                fipa_msg.query, fipa_msg.counterparty
            )
            fipa_dialogue.data_for_sale = data_for_sale
            fipa_dialogue.terms = terms
            self.context.logger.info(
                "[{}]: sending a PROPOSE with proposal={} to sender={}".format(
                    self.context.agent_name, proposal.values, fipa_msg.counterparty[-5:]
                )
            )
            proposal_msg = FipaMessage(
                performative=FipaMessage.Performative.PROPOSE,
                message_id=fipa_msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=fipa_msg.message_id,
                proposal=proposal,
            )
            proposal_msg.counterparty = fipa_msg.counterparty
            fipa_dialogue.update(proposal_msg)
            self.context.outbox.put_message(message=proposal_msg)
        else:
            self.context.logger.info(
                "[{}]: declined the CFP from sender={}".format(
                    self.context.agent_name, fipa_msg.counterparty[-5:]
                )
            )
            decline_msg = FipaMessage(
                message_id=fipa_msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=fipa_msg.message_id,
                performative=FipaMessage.Performative.DECLINE,
            )
            decline_msg.counterparty = fipa_msg.counterparty
            fipa_dialogue.update(decline_msg)
            self.context.outbox.put_message(message=decline_msg)
```

The above code will respond with a `Proposal` to the buyer if the CFP matches the supplied services and our strategy otherwise it will respond with a `Decline` message. 

The next code-block  handles the decline message we receive from the buyer. Add the following code below the `_handle_cfp`function:

``` python 
    def _handle_decline(
        self,
        fipa_msg: FipaMessage,
        fipa_dialogue: FipaDialogue,
        fipa_dialogues: FipaDialogues,
    ) -> None:
        """
        Handle the DECLINE.

        Close the dialogue.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received DECLINE from sender={}".format(
                self.context.agent_name, fipa_msg.counterparty[-5:]
            )
        )
        fipa_dialogues.dialogue_stats.add_dialogue_endstate(
            FipaDialogue.EndState.DECLINED_PROPOSE, fipa_dialogue.is_self_initiated
        )
```
If we receive a decline message from the buyer we close the dialogue and terminate this conversation with the `my_generic_buyer`.

Alternatively, we might receive an `Accept` message. In order to handle this option add the following code below the `_handle_decline` function:

``` python
    def _handle_accept(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the ACCEPT.

        Respond with a MATCH_ACCEPT_W_INFORM which contains the address to send the funds to.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received ACCEPT from sender={}".format(
                self.context.agent_name, fipa_msg.counterparty[-5:]
            )
        )
        match_accept_msg = FipaMessage(
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            message_id=fipa_msg.message_id + 1,
            dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
            target=fipa_msg.message_id,
            info={"address": fipa_dialogue.terms.sender_address},
        )
        self.context.logger.info(
            "[{}]: sending MATCH_ACCEPT_W_INFORM to sender={} with info={}".format(
                self.context.agent_name,
                fipa_msg.counterparty[-5:],
                match_accept_msg.info,
            )
        )
        match_accept_msg.counterparty = fipa_msg.counterparty
        fipa_dialogue.update(match_accept_msg)
        self.context.outbox.put_message(message=match_accept_msg)
```
When the `my_generic_buyer` accepts the `Proposal` we send it, and therefores sends us an `ACCEPT` message, we have to respond with another message (`MATCH_ACCEPT_W_INFORM` ) to inform the buyer about the address we would like it to send the funds to.

Lastly, we handle the `INFORM` message, which the buyer uses to inform us that it has sent the funds to the provided address. Add the following code:

``` python
    def _handle_inform(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the INFORM.

        If the INFORM message contains the transaction_digest then verify that it is settled, otherwise do nothing.
        If the transaction is settled, send the data, otherwise do nothing.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        new_message_id = fipa_msg.message_id + 1
        new_target = fipa_msg.message_id
        self.context.logger.info(
            "[{}]: received INFORM from sender={}".format(
                self.context.agent_name, fipa_msg.counterparty[-5:]
            )
        )

        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_ledger_tx and "transaction_digest" in fipa_msg.info.keys():
            self.context.logger.info(
                "[{}]: checking whether transaction={} has been received ...".format(
                    self.context.agent_name, fipa_msg.info["transaction_digest"]
                )
            )
            ledger_api_dialogues = cast(
                LedgerApiDialogues, self.context.ledger_api_dialogues
            )
            ledger_api_msg = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
                transaction_digest=TransactionDigest(
                    fipa_dialogue.terms.ledger_id, fipa_msg.info["transaction_digest"]
                ),
            )
            ledger_api_msg.counterparty = LEDGER_API_ADDRESS
            ledger_api_dialogue = cast(
                Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
            )
            assert (
                ledger_api_dialogue is not None
            ), "LedgerApiDialogue construction failed."
            ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
            self.context.outbox.put_message(message=ledger_api_msg)
        elif strategy.is_ledger_tx:
            self.context.logger.warning(
                "[{}]: did not receive transaction digest from sender={}.".format(
                    self.context.agent_name, fipa_msg.counterparty[-5:]
                )
            )
        elif not strategy.is_ledger_tx and "Done" in fipa_msg.info.keys():
            inform_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FipaMessage.Performative.INFORM,
                info=fipa_dialogue.data_for_sale,
            )
            inform_msg.counterparty = fipa_msg.counterparty
            fipa_dialogue.update(inform_msg)
            self.context.outbox.put_message(message=inform_msg)
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, fipa_dialogue.is_self_initiated
            )
            self.context.logger.info(
                "[{}]: transaction confirmed, sending data={} to buyer={}.".format(
                    self.context.agent_name,
                    fipa_dialogue.data_for_sale,
                    fipa_msg.counterparty[-5:],
                )
            )
        else:
            self.context.logger.warning(
                "[{}]: did not receive transaction confirmation from sender={}.".format(
                    self.context.agent_name, fipa_msg.counterparty[-5:]
                )
            )
```
We are checking the inform message. If it contains the transaction digest we verify that transaction matches the proposal that the buyer accepted. If the transaction is valid and we received the funds then we send the data to the buyer.  Otherwise we do not send the data.

The remaining handlers are as follows:
``` python
    def _handle_invalid(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle a fipa message of invalid performative.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle fipa message of performative={} in dialogue={}.".format(
                self.context.agent_name, fipa_msg.performative, fipa_dialogue
            )
        )


class GenericLedgerApiHandler(Handler):
    """Implement the ledger handler."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        ledger_api_msg = cast(LedgerApiMessage, message)

        # recover dialogue
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_dialogue = cast(
            Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
        )
        if ledger_api_dialogue is None:
            self._handle_unidentified_dialogue(ledger_api_msg)
            return

        # handle message
        if ledger_api_msg.performative is LedgerApiMessage.Performative.BALANCE:
            self._handle_balance(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            is LedgerApiMessage.Performative.TRANSACTION_RECEIPT
        ):
            self._handle_transaction_receipt(ledger_api_msg, ledger_api_dialogue)
        elif ledger_api_msg.performative == LedgerApiMessage.Performative.ERROR:
            self._handle_error(ledger_api_msg, ledger_api_dialogue)
        else:
            self._handle_invalid(ledger_api_msg, ledger_api_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid ledger_api message={}, unidentified dialogue.".format(
                self.context.agent_name, ledger_api_msg
            )
        )

    def _handle_balance(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: starting balance on {} ledger={}.".format(
                self.context.agent_name,
                ledger_api_msg.ledger_id,
                ledger_api_msg.balance,
            )
        )

    def _handle_transaction_receipt(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        fipa_dialogue = ledger_api_dialogue.associated_fipa_dialogue
        is_settled = LedgerApis.is_transaction_settled(
            fipa_dialogue.terms.ledger_id, ledger_api_msg.transaction_receipt.receipt
        )
        is_valid = LedgerApis.is_transaction_valid(
            fipa_dialogue.terms.ledger_id,
            ledger_api_msg.transaction_receipt.transaction,
            fipa_dialogue.terms.sender_address,
            fipa_dialogue.terms.counterparty_address,
            fipa_dialogue.terms.nonce,
            fipa_dialogue.terms.counterparty_payable_amount,
        )
        if is_settled and is_valid:
            last_message = cast(
                Optional[FipaMessage], fipa_dialogue.last_incoming_message
            )
            assert last_message is not None, "Cannot retrieve last fipa message."
            inform_msg = FipaMessage(
                message_id=last_message.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=last_message.message_id,
                performative=FipaMessage.Performative.INFORM,
                info=fipa_dialogue.data_for_sale,
            )
            inform_msg.counterparty = last_message.counterparty
            fipa_dialogue.update(inform_msg)
            self.context.outbox.put_message(message=inform_msg)
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, fipa_dialogue.is_self_initiated
            )
            self.context.logger.info(
                "[{}]: transaction confirmed, sending data={} to buyer={}.".format(
                    self.context.agent_name,
                    fipa_dialogue.data_for_sale,
                    last_message.counterparty[-5:],
                )
            )
        else:
            self.context.logger.info(
                "[{}]: transaction_receipt={} not settled or not valid, aborting".format(
                    self.context.agent_name, ledger_api_msg.transaction_receipt
                )
            )

    def _handle_error(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of error performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: received ledger_api error message={} in dialogue={}.".format(
                self.context.agent_name, ledger_api_msg, ledger_api_dialogue
            )
        )

    def _handle_invalid(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of invalid performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "[{}]: cannot handle ledger_api message of performative={} in dialogue={}.".format(
                self.context.agent_name,
                ledger_api_msg.performative,
                ledger_api_dialogue,
            )
        )


class GenericOefSearchHandler(Handler):
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
        oef_search_msg = cast(OefSearchMessage, message)

        # recover dialogue
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_dialogue = cast(
            Optional[OefSearchDialogue], oef_search_dialogues.update(oef_search_msg)
        )
        if oef_search_dialogue is None:
            self._handle_unidentified_dialogue(oef_search_msg)
            return

        # handle message
        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid oef_search message={}, unidentified dialogue.".format(
                self.context.agent_name, oef_search_msg
            )
        )

    def _handle_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "[{}]: received oef_search error message={} in dialogue={}.".format(
                self.context.agent_name, oef_search_msg, oef_search_dialogue
            )
        )

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle oef_search message of performative={} in dialogue={}.".format(
                self.context.agent_name,
                oef_search_msg.performative,
                oef_search_dialogue,
            )
        )
```


### Step 4: Create the strategy

Next, we are going to create the strategy that we want our `my_generic_seller` AEA to follow. Rename the `my_model.py` file (`my_generic_seller/skills/generic_seller/my_model.py`) to `strategy.py` and copy and paste the following code: 

``` python 
import uuid
from typing import Any, Dict, Optional, Tuple

from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.search.generic import GenericDataModel
from aea.helpers.search.models import Description, Query
from aea.helpers.transaction.base import Terms
from aea.mail.base import Address
from aea.skills.base import Model

DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_IS_LEDGER_TX = True

DEFAULT_CURRENCY_ID = "FET"
DEFAULT_UNIT_PRICE = 4
DEFAULT_SERVICE_ID = "generic_service"

DEFAULT_SERVICE_DATA = {"country": "UK", "city": "Cambridge"}
DEFAULT_DATA_MODEL = {
    "attribute_one": {"name": "country", "type": "str", "is_required": True},
    "attribute_two": {"name": "city", "type": "str", "is_required": True},
}  # type: Optional[Dict[str, Any]]
DEFAULT_DATA_MODEL_NAME = "location"

DEFAULT_HAS_DATA_SOURCE = False
DEFAULT_DATA_FOR_SALE = {
    "some_generic_data_key": "some_generic_data_value"
}  # type: Optional[Dict[str, Any]]


class GenericStrategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self._is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)

        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_ID)
        self._unit_price = kwargs.pop("unit_price", DEFAULT_UNIT_PRICE)
        self._service_id = kwargs.pop("service_id", DEFAULT_SERVICE_ID)

        self._service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        self._data_model = kwargs.pop("data_model", DEFAULT_DATA_MODEL)
        self._data_model_name = kwargs.pop("data_model_name", DEFAULT_DATA_MODEL_NAME)

        self._has_data_source = kwargs.pop("has_data_source", DEFAULT_HAS_DATA_SOURCE)
        data_for_sale_ordered = kwargs.pop("data_for_sale", DEFAULT_DATA_FOR_SALE)
        data_for_sale = {
            str(key): str(value) for key, value in data_for_sale_ordered.items()
        }

        super().__init__(**kwargs)
        assert (
            self.context.agent_addresses.get(self._ledger_id, None) is not None
        ), "Wallet does not contain cryptos for provided ledger id."

        if self._has_data_source:
            self._data_for_sale = self.collect_from_data_source()
        else:
            self._data_for_sale = data_for_sale
        self._sale_quantity = len(data_for_sale)
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

    @property
    def is_ledger_tx(self) -> bool:
        """Check whether or not tx are settled on a ledger."""
        return self._is_ledger_tx

    def get_service_description(self) -> Description:
        """
        Get the service description.

        :return: a description of the offered services
        """
        description = Description(
            self._service_data,
            data_model=GenericDataModel(self._data_model_name, self._data_model),
        )
        return description

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indiciating whether matches or not
        """
        return query.check(self.get_service_description())

    def generate_proposal_terms_and_data(
        self, query: Query, counterparty_address: Address
    ) -> Tuple[Description, Terms, Dict[str, str]]:
        """
        Generate a proposal matching the query.

        :param query: the query
        :param counterparty_address: the counterparty of the proposal.
        :return: a tuple of proposal, terms and the weather data
        """
        seller_address = self.context.agent_addresses[self.ledger_id]
        total_price = self._sale_quantity * self._unit_price
        if self.is_ledger_tx:
            tx_nonce = LedgerApis.generate_tx_nonce(
                identifier=self.ledger_id,
                seller=seller_address,
                client=counterparty_address,
            )
        else:
            tx_nonce = uuid.uuid4().hex
        proposal = Description(
            {
                "ledger_id": self.ledger_id,
                "price": total_price,
                "currency_id": self._currency_id,
                "service_id": self._service_id,
                "quantity": self._sale_quantity,
                "tx_nonce": tx_nonce,
            }
        )
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=seller_address,
            counterparty_address=counterparty_address,
            amount_by_currency_id={self._currency_id: total_price},
            quantities_by_good_id={self._service_id: -self._sale_quantity},
            is_sender_payable_tx_fee=False,
            nonce=tx_nonce,
            fee_by_currency_id={self._currency_id: 0},
        )
        return proposal, terms, self._data_for_sale

    def collect_from_data_source(self) -> Dict[str, str]:
        """Implement the logic to communicate with the sensor."""
        raise NotImplementedError
```

Before the creation of the actual proposal, we have to check if the sale generates value for us or a loss. If it is a loss, we abort and warn the developer. The helper private function `_build_data_payload`, is where we read data from our sensor or in case we do not have a sensor generate a random number.

### Step 5: Create the dialogues

When we are negotiating with other AEAs we would like to keep track of the state of these negotiations. To this end we create a new file in the skill folder (`my_generic_seller/skills/generic_seller/`) and name it `dialogues.py`. Inside this file add the following code: 

``` python
from typing import Dict, Optional

from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.helpers.transaction.base import Terms
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.protocols.default.dialogues import DefaultDialogue as BaseDefaultDialogue
from aea.protocols.default.dialogues import DefaultDialogues as BaseDefaultDialogues
from aea.skills.base import Model

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue as BaseFipaDialogue
from packages.fetchai.protocols.fipa.dialogues import FipaDialogues as BaseFipaDialogues
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogue as BaseLedgerApiDialogue,
)
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)

DefaultDialogue = BaseDefaultDialogue


class DefaultDialogues(Model, BaseDefaultDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseDefaultDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return DefaultDialogue.Role.AGENT

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> DefaultDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = DefaultDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


class FipaDialogue(BaseFipaDialogue):
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
        BaseFipaDialogue.__init__(
            self, dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )
        self.data_for_sale = None  # type: Optional[Dict[str, str]]
        self._terms = None  # type: Optional[Terms]

    @property
    def terms(self) -> Terms:
        """Get terms."""
        assert self._terms is not None, "Terms not set!"
        return self._terms

    @terms.setter
    def terms(self, terms: Terms) -> None:
        """Set terms."""
        assert self._terms is None, "Terms already set!"
        self._terms = terms


class FipaDialogues(Model, BaseFipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseFipaDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """
        Infer the role of the agent from an incoming or outgoing first message

        :param message: an incoming/outgoing first message
        :return: the agent's role
        """
        return FipaDialogue.Role.SELLER

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> FipaDialogue:
        """
        Create an instance of dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = FipaDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


class LedgerApiDialogue(BaseLedgerApiDialogue):
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
        BaseLedgerApiDialogue.__init__(
            self, dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )
        self._associated_fipa_dialogue = None  # type: Optional[FipaDialogue]

    @property
    def associated_fipa_dialogue(self) -> FipaDialogue:
        """Get associated_fipa_dialogue."""
        assert self._associated_fipa_dialogue is not None, "FipaDialogue not set!"
        return self._associated_fipa_dialogue

    @associated_fipa_dialogue.setter
    def associated_fipa_dialogue(self, fipa_dialogue: FipaDialogue) -> None:
        """Set associated_fipa_dialogue"""
        assert self._associated_fipa_dialogue is None, "FipaDialogue already set!"
        self._associated_fipa_dialogue = fipa_dialogue


class LedgerApiDialogues(Model, BaseLedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseLedgerApiDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return BaseLedgerApiDialogue.Role.AGENT

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> LedgerApiDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = LedgerApiDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


OefSearchDialogue = BaseOefSearchDialogue


class OefSearchDialogues(Model, BaseOefSearchDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseOefSearchDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return BaseOefSearchDialogue.Role.AGENT

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> OefSearchDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = OefSearchDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue
```

The `Dialogues` class stores dialogue with each `my_generic_buyer` (and other AEAs) and exposes a number of helpful methods to manage them. This helps us match messages to a dialogue, access previous messages and enable us to identify possible communications problems between the `my_generic_seller` AEA and the `my_generic_buyer` AEA. It also keeps track of the data that we offer for sale during the proposal phase.

The `Dialogues` class extends `FipaDialogues`, which itself derives from the base <a href="../api/helpers/dialogue/base#dialogues-objects">`Dialogues`</a> class. Similarly, the `Dialogue` class extends `FipaDialogue`, which itself derives from the base <a href="../api/helpers/dialogue/base#dialogue-objects">`Dialogue`</a> class. To learn more about dialogues have a look <a href="../protocol">here</a>.

### Step 6: Update the YAML files

Since we made so many changes to our AEA we have to update the `skill.yaml` (at `my_generic_seller/skills/generic_seller/skill.yaml`). Make sure that your `skill.yaml` matches with the following code 

``` yaml
name: generic_seller
author: fetchai
version: 0.6.0
description: The weather station skill implements the functionality to sell weather
  data.
license: Apache-2.0
aea_version: '>=0.5.0, <0.6.0'
fingerprint:
  __init__.py: QmbfkeFnZVKppLEHpBrTXUXBwg2dpPABJWSLND8Lf1cmpG
  behaviours.py: QmTwUHrRrBvadNp4RBBEKcMBUvgv2MuGojz7gDsuYDrauE
  dialogues.py: QmY44eSrEzaZxtAG1dqbddwouj5iVMEitzpmt2xFC6MDUm
  handlers.py: QmSiquvAA4ULXPEJfmT3Z85Lqm9Td2H2uXXKuXrZjcZcPK
  strategy.py: QmYt74ucz8GfddfwP5dFgQBbD1dkcWvydUyEZ8jn9uxEDK
fingerprint_ignore_patterns: []
contracts: []
protocols:
- fetchai/default:0.3.0
- fetchai/fipa:0.4.0
- fetchai/ledger_api:0.1.0
- fetchai/oef_search:0.3.0
skills: []
behaviours:
  service_registration:
    args:
      services_interval: 20
    class_name: GenericServiceRegistrationBehaviour
handlers:
  fipa:
    args: {}
    class_name: GenericFipaHandler
  ledger_api:
    args: {}
    class_name: GenericLedgerApiHandler
  oef_search:
    args: {}
    class_name: GenericOefSearchHandler
models:
  default_dialogues:
    args: {}
    class_name: DefaultDialogues
  fipa_dialogues:
    args: {}
    class_name: FipaDialogues
  ledger_api_dialogues:
    args: {}
    class_name: LedgerApiDialogues
  oef_search_dialogues:
    args: {}
    class_name: OefSearchDialogues
  strategy:
    args:
      currency_id: FET
      data_for_sale:
        generic: data
      data_model:
        attribute_one:
          is_required: true
          name: country
          type: str
        attribute_two:
          is_required: true
          name: city
          type: str
      data_model_name: location
      has_data_source: false
      is_ledger_tx: true
      ledger_id: fetchai
      service_data:
        city: Cambridge
        country: UK
      service_id: generic_service
      unit_price: 10
    class_name: GenericStrategy
dependencies: {}
```

We must pay attention to the models and in particular the strategy’s variables. Here we can change the price we would like to sell each reading for or the currency we would like to transact with. Lastly, the dependencies are the third party packages we need to install in order to get readings from the sensor. 

Finally, we fingerprint our new skill:

``` bash
aea fingerprint skill generic_seller
```

This will hash each file and save the hash in the fingerprint. This way, in the future we can easily track if any of the files have changed.


## Generic Buyer AEA

### Step 1: Create the AEA

Create a new AEA by typing the following command in the terminal:

``` bash
aea create my_generic_buyer
cd my_generic_buyer
```

Our newly created AEA is inside the current working directory. Let’s create our new skill that will handle the purchase of the data. Type the following command:

``` bash
aea scaffold skill generic_buyer
```

This command will create the correct structure for a new skill inside our AEA project You can locate the newly created skill inside the skills folder (`my_generic_buyer/skills/generic_buyer/`) and it must contain the following files:

- `behaviours.py`
- `handlers.py`
- `my_model.py`
- `skills.yaml`
- `__init__.py`

### Step 2: Create the behaviour

A <a href="../api/skills/base#behaviour-objects">`Behaviour`</a> class contains the business logic specific to actions initiated by the AEA rather than reactions to other events.

Open the `behaviours.py` (`my_generic_buyer/skills/generic_buyer/behaviours.py`) and add the following code:

``` python 
from typing import cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.dialogues import (
    LedgerApiDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy

DEFAULT_SEARCH_INTERVAL = 5.0
LEDGER_API_ADDRESS = "fetchai/ledger:0.1.0"


class GenericSearchBehaviour(TickerBehaviour):
    """This class implements a search behaviour."""

    def __init__(self, **kwargs):
        """Initialize the search behaviour."""
        search_interval = cast(
            float, kwargs.pop("search_interval", DEFAULT_SEARCH_INTERVAL)
        )
        super().__init__(tick_interval=search_interval, **kwargs)

    def setup(self) -> None:
        """Implement the setup for the behaviour."""
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_ledger_tx:
            ledger_api_dialogues = cast(
                LedgerApiDialogues, self.context.ledger_api_dialogues
            )
            ledger_api_msg = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_BALANCE,
                dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
                ledger_id=strategy.ledger_id,
                address=cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
            )
            ledger_api_msg.counterparty = LEDGER_API_ADDRESS
            ledger_api_dialogues.update(ledger_api_msg)
            self.context.outbox.put_message(message=ledger_api_msg)
        else:
            strategy.is_searching = True

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_searching:
            query = strategy.get_service_query()
            oef_search_dialogues = cast(
                OefSearchDialogues, self.context.oef_search_dialogues
            )
            oef_search_msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
                query=query,
            )
            oef_search_msg.counterparty = self.context.search_service_address
            oef_search_dialogues.update(oef_search_msg)
            self.context.outbox.put_message(message=oef_search_msg)

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
```

This <a href="../api/skills/behaviours#tickerbehaviour-objects">`TickerBehaviour`</a> will search on  the[OEF search node](../oef-ledger) with a specific query at regular tick intervals. 

### Step 3: Create the handler

So far, we have tasked the AEA with sending search queries to the [OEF search node](../oef-ledger). However, we have at present no way of handling the responses sent to the AEA by the [OEF search node](../oef-ledger) or messages sent by other agent.

Let us now implement a <a href="../api/skills/base#handler-objects">`Handler`</a> to deal with the incoming messages. Open the `handlers.py` file (`my_generic_buyer/skills/generic_buyer/handlers.py`) and add the following code:

``` python
import pprint
from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.signing.message import SigningMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.dialogues import (
    DefaultDialogues,
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy

LEDGER_API_ADDRESS = "fetchai/ledger:0.1.0"


class GenericFipaHandler(Handler):
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
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        fipa_dialogue = cast(FipaDialogue, fipa_dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FipaMessage.Performative.PROPOSE:
            self._handle_propose(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, fipa_dialogue, fipa_dialogues)
        elif fipa_msg.performative == FipaMessage.Performative.MATCH_ACCEPT_W_INFORM:
            self._handle_match_accept(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, fipa_dialogue, fipa_dialogues)
        else:
            self._handle_invalid(fipa_msg, fipa_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
```
You will see that we are following similar logic to the `generic_seller` when we develop the `generic_buyer`’s side of the negotiation. First, we create a new dialogue and we store it in the dialogues class. Then we are checking what kind of message we received. So lets start creating our handlers:

``` python 
    def _handle_unidentified_dialogue(self, fipa_msg: FipaMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param fipa_msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid fipa message={}, unidentified dialogue.".format(
                self.context.agent_name, fipa_msg
            )
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg = DefaultMessage(
            performative=DefaultMessage.Performative.ERROR,
            dialogue_reference=default_dialogues.new_self_initiated_dialogue_reference(),
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": fipa_msg.encode()},
        )
        default_msg.counterparty = fipa_msg.counterparty
        default_dialogues.update(default_msg)
        self.context.outbox.put_message(message=default_msg)
```
The above code handles the unidentified dialogues. And responds with an error message to the sender. Next we will handle the `Proposal` that we receive from the `my_generic_seller` AEA: 

``` python
    def _handle_propose(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the propose.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received proposal={} from sender={}".format(
                self.context.agent_name,
                fipa_msg.proposal.values,
                fipa_msg.counterparty[-5:],
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        acceptable = strategy.is_acceptable_proposal(fipa_msg.proposal)
        affordable = strategy.is_affordable_proposal(fipa_msg.proposal)
        if acceptable and affordable:
            self.context.logger.info(
                "[{}]: accepting the proposal from sender={}".format(
                    self.context.agent_name, fipa_msg.counterparty[-5:]
                )
            )
            terms = strategy.terms_from_proposal(
                fipa_msg.proposal, fipa_msg.counterparty
            )
            fipa_dialogue.terms = terms
            accept_msg = FipaMessage(
                message_id=fipa_msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=fipa_msg.message_id,
                performative=FipaMessage.Performative.ACCEPT,
            )
            accept_msg.counterparty = fipa_msg.counterparty
            fipa_dialogue.update(accept_msg)
            self.context.outbox.put_message(message=accept_msg)
        else:
            self.context.logger.info(
                "[{}]: declining the proposal from sender={}".format(
                    self.context.agent_name, fipa_msg.counterparty[-5:]
                )
            )
            decline_msg = FipaMessage(
                message_id=fipa_msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=fipa_msg.message_id,
                performative=FipaMessage.Performative.DECLINE,
            )
            decline_msg.counterparty = fipa_msg.counterparty
            fipa_dialogue.update(decline_msg)
            self.context.outbox.put_message(message=decline_msg)
```
When we receive a proposal we have to check if we have the funds to complete the transaction and if the proposal is acceptable based on our strategy. If the proposal is not affordable or acceptable we respond with a `DECLINE` message. Otherwise, we send an `ACCEPT` message to the seller.

The next code-block handles the `DECLINE` message that we may receive from the buyer on our `CFP`message or our `ACCEPT` message:

``` python
    def _handle_decline(
        self,
        fipa_msg: FipaMessage,
        fipa_dialogue: FipaDialogue,
        fipa_dialogues: FipaDialogues,
    ) -> None:
        """
        Handle the decline.

        :param fipa_msg: the message
        :param fipa_dialogue: the fipa dialogue
        :param fipa_dialogues: the fipa dialogues
        :return: None
        """
        self.context.logger.info(
            "[{}]: received DECLINE from sender={}".format(
                self.context.agent_name, fipa_msg.counterparty[-5:]
            )
        )
        if fipa_msg.target == 1:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_CFP, fipa_dialogue.is_self_initiated
            )
        elif fipa_msg.target == 3:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_ACCEPT, fipa_dialogue.is_self_initiated
            )
```
The above code terminates each dialogue with the specific AEA and stores the step. For example, if the `target == 1` we know that the seller declined our `CFP` message.

In case we do not receive any `DECLINE` message that means that the `my_generic_seller` AEA want to move on with the sale, in that case, it will send a `MATCH_ACCEPT` message. In order to handle this we add the following code: 

``` python
    def _handle_match_accept(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the match accept.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received MATCH_ACCEPT_W_INFORM from sender={} with info={}".format(
                self.context.agent_name, fipa_msg.counterparty[-5:], fipa_msg.info
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_ledger_tx:
            transfer_address = fipa_msg.info.get("address", None)
            if transfer_address is not None and isinstance(transfer_address, str):
                fipa_dialogue.terms.counterparty_address = transfer_address
            ledger_api_dialogues = cast(
                LedgerApiDialogues, self.context.ledger_api_dialogues
            )
            ledger_api_msg = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
                dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
                terms=fipa_dialogue.terms,
            )
            ledger_api_msg.counterparty = LEDGER_API_ADDRESS
            ledger_api_dialogue = cast(
                Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
            )
            assert (
                ledger_api_dialogue is not None
            ), "Error when creating ledger api dialogue."
            ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
            fipa_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
            self.context.outbox.put_message(message=ledger_api_msg)
            self.context.logger.info(
                "[{}]: requesting transfer transaction from ledger api...".format(
                    self.context.agent_name
                )
            )
        else:
            inform_msg = FipaMessage(
                message_id=fipa_msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=fipa_msg.message_id,
                performative=FipaMessage.Performative.INFORM,
                info={"Done": "Sending payment via bank transfer"},
            )
            inform_msg.counterparty = fipa_msg.counterparty
            fipa_dialogue.update(inform_msg)
            self.context.outbox.put_message(message=inform_msg)
            self.context.logger.info(
                "[{}]: informing counterparty={} of payment.".format(
                    self.context.agent_name, fipa_msg.counterparty[-5:]
                )
            )
```
The first thing we are checking is if we enabled our AEA to transact with a ledger. If we can transact with a ledger we generate a transaction message and we propose it to the `DecisionMaker` (more on the `DecisionMaker` <a href="../decision-maker">here</a>. The `DecisionMaker` then will check the transaction message. If it is acceptable (i.e. we have the funds, etc) it signs and sends the transaction to the specified ledger. Then it returns us the transaction digest.

Lastly, we need to handle the `INFORM` message. This is the message that will have our data:

``` python
    def _handle_inform(
        self,
        fipa_msg: FipaMessage,
        fipa_dialogue: FipaDialogue,
        fipa_dialogues: FipaDialogues,
    ) -> None:
        """
        Handle the match inform.

        :param fipa_msg: the message
        :param fipa_dialogue: the fipa dialogue
        :param fipa_dialogues: the fipa dialogues
        :return: None
        """
        self.context.logger.info(
            "[{}]: received INFORM from sender={}".format(
                self.context.agent_name, fipa_msg.counterparty[-5:]
            )
        )
        if len(fipa_msg.info.keys()) >= 1:
            data = fipa_msg.info
            self.context.logger.info(
                "[{}]: received the following data={}".format(
                    self.context.agent_name, pprint.pformat(data)
                )
            )
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, fipa_dialogue.is_self_initiated
            )
        else:
            self.context.logger.info(
                "[{}]: received no data from sender={}".format(
                    self.context.agent_name, fipa_msg.counterparty[-5:]
                )
            )

    def _handle_invalid(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle a fipa message of invalid performative.

        :param fipa_msg: the message
        :param fipa_dialogue: the fipa dialogue
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle fipa message of performative={} in dialogue={}.".format(
                self.context.agent_name, fipa_msg.performative, fipa_dialogue
            )
        )
```
The main difference between the `generic_buyer` and the `generic_seller` skill `handlers.py` file is that in this one we create more than one handler.

The reason is that we receive messages not only from the `my_generic_seller` AEA but also from the `DecisionMaker` and the [OEF search node](../oef-ledger). We need one handler for each type of protocol we use.

To handle the messages in the `oef_search` protocol used by the [OEF search node](../oef-ledger) we add the following code in the same file (`my_generic_buyer/skills/generic_buyer/handlers.py`):

``` python 
class GenericOefSearchHandler(Handler):
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
        oef_search_msg = cast(OefSearchMessage, message)

        # recover dialogue
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_dialogue = cast(
            Optional[OefSearchDialogue], oef_search_dialogues.update(oef_search_msg)
        )
        if oef_search_dialogue is None:
            self._handle_unidentified_dialogue(oef_search_msg)
            return

        # handle message
        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            self._handle_search(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid oef_search message={}, unidentified dialogue.".format(
                self.context.agent_name, oef_search_msg
            )
        )

    def _handle_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "[{}]: received oef_search error message={} in dialogue={}.".format(
                self.context.agent_name, oef_search_msg, oef_search_dialogue
            )
        )

    def _handle_search(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :return: None
        """
        if len(oef_search_msg.agents) == 0:
            self.context.logger.info(
                "[{}]: found no agents, continue searching.".format(
                    self.context.agent_name
                )
            )
            return

        self.context.logger.info(
            "[{}]: found agents={}, stopping search.".format(
                self.context.agent_name,
                list(map(lambda x: x[-5:], oef_search_msg.agents)),
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        strategy.is_searching = False  # stopping search
        query = strategy.get_service_query()
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        for idx, counterparty in enumerate(oef_search_msg.agents):
            if idx >= strategy.max_negotiations:
                continue
            cfp_msg = FipaMessage(
                performative=FipaMessage.Performative.CFP,
                dialogue_reference=fipa_dialogues.new_self_initiated_dialogue_reference(),
                query=query,
            )
            cfp_msg.counterparty = counterparty
            fipa_dialogues.update(cfp_msg)
            self.context.outbox.put_message(message=cfp_msg)
            self.context.logger.info(
                "[{}]: sending CFP to agent={}".format(
                    self.context.agent_name, counterparty[-5:]
                )
            )

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle oef_search message of performative={} in dialogue={}.".format(
                self.context.agent_name,
                oef_search_msg.performative,
                oef_search_dialogue,
            )
        )
```
When we receive a message from the [OEF search node](../oef-ledger) of a type `OefSearchMessage.Performative.SEARCH_RESULT`, we are passing the details to the relevant handler method. In the `_handle_search` function we are checking that the response contains some agents and we stop the search if it does. We pick our first agent and we send a `CFP` message.

The last handler we need is the `MyTransactionHandler`. This handler will handle the internal messages that we receive from the `DecisionMaker`.

``` python 
class GenericSigningHandler(Handler):
    """Implement the signing handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        signing_msg = cast(SigningMessage, message)

        # recover dialogue
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_dialogue = cast(
            Optional[SigningDialogue], signing_dialogues.update(signing_msg)
        )
        if signing_dialogue is None:
            self._handle_unidentified_dialogue(signing_msg)
            return

        # handle message
        if signing_msg.performative is SigningMessage.Performative.SIGNED_TRANSACTION:
            self._handle_signed_transaction(signing_msg, signing_dialogue)
        elif signing_msg.performative is SigningMessage.Performative.ERROR:
            self._handle_error(signing_msg, signing_dialogue)
        else:
            self._handle_invalid(signing_msg, signing_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, signing_msg: SigningMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid signing message={}, unidentified dialogue.".format(
                self.context.agent_name, signing_msg
            )
        )

    def _handle_signed_transaction(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "[{}]: transaction signing was successful.".format(self.context.agent_name)
        )
        fipa_dialogue = signing_dialogue.associated_fipa_dialogue
        ledger_api_dialogue = fipa_dialogue.associated_ledger_api_dialogue
        last_ledger_api_msg = ledger_api_dialogue.last_incoming_message
        assert (
            last_ledger_api_msg is not None
        ), "Could not retrieve last message in ledger api dialogue"
        ledger_api_msg = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            dialogue_reference=ledger_api_dialogue.dialogue_label.dialogue_reference,
            target=last_ledger_api_msg.message_id,
            message_id=last_ledger_api_msg.message_id + 1,
            signed_transaction=signing_msg.signed_transaction,
        )
        ledger_api_msg.counterparty = LEDGER_API_ADDRESS
        ledger_api_dialogue.update(ledger_api_msg)
        self.context.outbox.put_message(message=ledger_api_msg)
        self.context.logger.info(
            "[{}]: sending transaction to ledger.".format(self.context.agent_name)
        )

    def _handle_error(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "[{}]: transaction signing was not successful. Error_code={} in dialogue={}".format(
                self.context.agent_name, signing_msg.error_code, signing_dialogue
            )
        )

    def _handle_invalid(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle signing message of performative={} in dialogue={}.".format(
                self.context.agent_name, signing_msg.performative, signing_dialogue
            )
        )


class GenericLedgerApiHandler(Handler):
    """Implement the ledger handler."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        ledger_api_msg = cast(LedgerApiMessage, message)

        # recover dialogue
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_dialogue = cast(
            Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
        )
        if ledger_api_dialogue is None:
            self._handle_unidentified_dialogue(ledger_api_msg)
            return

        # handle message
        if ledger_api_msg.performative is LedgerApiMessage.Performative.BALANCE:
            self._handle_balance(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative is LedgerApiMessage.Performative.RAW_TRANSACTION
        ):
            self._handle_raw_transaction(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            == LedgerApiMessage.Performative.TRANSACTION_DIGEST
        ):
            self._handle_transaction_digest(ledger_api_msg, ledger_api_dialogue)
        elif ledger_api_msg.performative == LedgerApiMessage.Performative.ERROR:
            self._handle_error(ledger_api_msg, ledger_api_dialogue)
        else:
            self._handle_invalid(ledger_api_msg, ledger_api_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid ledger_api message={}, unidentified dialogue.".format(
                self.context.agent_name, ledger_api_msg
            )
        )

    def _handle_balance(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        strategy = cast(GenericStrategy, self.context.strategy)
        if ledger_api_msg.balance > 0:
            self.context.logger.info(
                "[{}]: starting balance on {} ledger={}.".format(
                    self.context.agent_name, strategy.ledger_id, ledger_api_msg.balance,
                )
            )
            strategy.balance = ledger_api_msg.balance
            strategy.is_searching = True
        else:
            self.context.logger.warning(
                "[{}]: you have no starting balance on {} ledger!".format(
                    self.context.agent_name, strategy.ledger_id
                )
            )
            self.context.is_active = False

    def _handle_raw_transaction(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of raw_transaction performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: received raw transaction={}".format(
                self.context.agent_name, ledger_api_msg
            )
        )
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(self.context.skill_id),),
            raw_transaction=ledger_api_msg.raw_transaction,
            terms=ledger_api_dialogue.associated_fipa_dialogue.terms,
            skill_callback_info={},
        )
        signing_msg.counterparty = "decision_maker"
        signing_dialogue = cast(
            Optional[SigningDialogue], signing_dialogues.update(signing_msg)
        )
        assert signing_dialogue is not None, "Error when creating signing dialogue"
        signing_dialogue.associated_fipa_dialogue = (
            ledger_api_dialogue.associated_fipa_dialogue
        )
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "[{}]: proposing the transaction to the decision maker. Waiting for confirmation ...".format(
                self.context.agent_name
            )
        )

    def _handle_transaction_digest(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction_digest performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        fipa_dialogue = ledger_api_dialogue.associated_fipa_dialogue
        self.context.logger.info(
            "[{}]: transaction was successfully submitted. Transaction digest={}".format(
                self.context.agent_name, ledger_api_msg.transaction_digest
            )
        )
        fipa_msg = cast(Optional[FipaMessage], fipa_dialogue.last_incoming_message)
        assert fipa_msg is not None, "Could not retrieve fipa message"
        inform_msg = FipaMessage(
            performative=FipaMessage.Performative.INFORM,
            message_id=fipa_msg.message_id + 1,
            dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
            target=fipa_msg.message_id,
            info={"transaction_digest": ledger_api_msg.transaction_digest.body},
        )
        inform_msg.counterparty = fipa_dialogue.dialogue_label.dialogue_opponent_addr
        fipa_dialogue.update(inform_msg)
        self.context.outbox.put_message(message=inform_msg)
        self.context.logger.info(
            "[{}]: informing counterparty={} of transaction digest.".format(
                self.context.agent_name,
                fipa_dialogue.dialogue_label.dialogue_opponent_addr[-5:],
            )
        )

    def _handle_error(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of error performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: received ledger_api error message={} in dialogue={}.".format(
                self.context.agent_name, ledger_api_msg, ledger_api_dialogue
            )
        )

    def _handle_invalid(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of invalid performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "[{}]: cannot handle ledger_api message of performative={} in dialogue={}.".format(
                self.context.agent_name,
                ledger_api_msg.performative,
                ledger_api_dialogue,
            )
        )
```
Remember that we send a message to the `DecisionMaker` with a transaction proposal. Here, we handle the response from the `DecisionMaker`.

If the message is of performative `SUCCESFUL_SETTLEMENT`, we generate the `INFORM` message for the `my_generic_seller` AEA to inform it that we completed the transaction and transferred the funds to the address that it sent us. We also pass along the transaction digest so the `my_generic_seller` AEA can verify the transaction.

If the transaction was unsuccessful, the `DecisionMaker` will inform us that something went wrong and the transaction was not successful.

### Step 4: Create the strategy

We are going to create the strategy that we want our AEA to follow. Rename the `my_model.py` file (in `my_generic_buyer/skills/generic_buyer/`) to `strategy.py` and paste the following code: 

``` python
from typing import Any, Dict, Optional

from aea.helpers.search.generic import GenericDataModel
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.helpers.transaction.base import Terms
from aea.mail.base import Address
from aea.skills.base import Model

DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_IS_LEDGER_TX = True

DEFAULT_CURRENCY_ID = "FET"
DEFAULT_MAX_UNIT_PRICE = 5
DEFAULT_MAX_TX_FEE = 2
DEFAULT_SERVICE_ID = "generic_service"

DEFAULT_SEARCH_QUERY = {
    "constraint_one": {
        "search_term": "country",
        "search_value": "UK",
        "constraint_type": "==",
    },
    "constraint_two": {
        "search_term": "city",
        "search_value": "Cambridge",
        "constraint_type": "==",
    },
}
DEFAULT_DATA_MODEL = {
    "attribute_one": {"name": "country", "type": "str", "is_required": True},
    "attribute_two": {"name": "city", "type": "str", "is_required": True},
}  # type: Optional[Dict[str, Any]]
DEFAULT_DATA_MODEL_NAME = "location"

DEFAULT_MAX_NEGOTIATIONS = 2


class GenericStrategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self._is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)

        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_ID)
        self._max_unit_price = kwargs.pop("max_unit_price", DEFAULT_MAX_UNIT_PRICE)
        self._max_tx_fee = kwargs.pop("max_tx_fee", DEFAULT_MAX_TX_FEE)
        self._service_id = kwargs.pop("service_id", DEFAULT_SERVICE_ID)

        self._search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        self._data_model = kwargs.pop("data_model", DEFAULT_DATA_MODEL)
        self._data_model_name = kwargs.pop("data_model_name", DEFAULT_DATA_MODEL_NAME)

        self._max_negotiations = kwargs.pop(
            "max_negotiations", DEFAULT_MAX_NEGOTIATIONS
        )

        super().__init__(**kwargs)
        self._is_searching = False
        self._balance = 0
```

We initialize the strategy class by trying to read the strategy variables from the YAML file. If this is not possible we specified some default values. The following two functions are related to the oef search service, add them under the initialization of the class:

``` python
    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def is_ledger_tx(self) -> bool:
        """Check whether or not tx are settled on a ledger."""
        return self._is_ledger_tx

    @property
    def is_searching(self) -> bool:
        """Check if the agent is searching."""
        return self._is_searching

    @is_searching.setter
    def is_searching(self, is_searching: bool) -> None:
        """Check if the agent is searching."""
        assert isinstance(is_searching, bool), "Can only set bool on is_searching!"
        self._is_searching = is_searching

    @property
    def balance(self) -> int:
        """Get the balance."""
        return self._balance

    @balance.setter
    def balance(self, balance: int) -> None:
        """Set the balance."""
        self._balance = balance

    @property
    def max_negotiations(self) -> int:
        """Get the maximum number of negotiations the agent can start."""
        return self._max_negotiations

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        query = Query(
            [
                Constraint(
                    constraint["search_term"],
                    ConstraintType(
                        constraint["constraint_type"], constraint["search_value"],
                    ),
                )
                for constraint in self._search_query.values()
            ],
            model=GenericDataModel(self._data_model_name, self._data_model),
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
            all(
                [
                    key in proposal.values
                    for key in [
                        "ledger_id",
                        "currency_id",
                        "price",
                        "service_id",
                        "quantity",
                        "tx_nonce",
                    ]
                ]
            )
            and proposal.values["ledger_id"] == self.ledger_id
            and proposal.values["price"]
            <= proposal.values["quantity"] * self._max_unit_price
            and proposal.values["currency_id"] == self._currency_id
            and proposal.values["service_id"] == self._service_id
            and isinstance(proposal.values["tx_nonce"], str)
            and proposal.values["tx_nonce"] != ""
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
            payable = proposal.values.get("price", 0) + self._max_tx_fee
            result = self.balance >= payable
        else:
            result = True
        return result

    def terms_from_proposal(
        self, proposal: Description, counterparty_address: Address
    ) -> Terms:
        """
        Get the terms from a proposal.

        :param proposal: the proposal
        :return: terms
        """
        buyer_address = self.context.agent_addresses[proposal.values["ledger_id"]]
        terms = Terms(
            ledger_id=proposal.values["ledger_id"],
            sender_address=buyer_address,
            counterparty_address=counterparty_address,
            amount_by_currency_id={
                proposal.values["currency_id"]: -proposal.values["price"]
            },
            quantities_by_good_id={
                proposal.values["service_id"]: proposal.values["quantity"]
            },
            is_sender_payable_tx_fee=True,
            nonce=proposal.values["tx_nonce"],
            fee_by_currency_id={proposal.values["currency_id"]: self._max_tx_fee},
        )
        return terms
```

### Step 5: Create the dialogues

As mentioned, when we are negotiating with other AEA we would like to keep track of these negotiations for various reasons. Create a new file and name it `dialogues.py` (in `my_generic_buyer/skills/generic_buyer/`). Inside this file add the following code: 

``` python
from typing import Optional

from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.helpers.transaction.base import Terms
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.protocols.default.dialogues import DefaultDialogue as BaseDefaultDialogue
from aea.protocols.default.dialogues import DefaultDialogues as BaseDefaultDialogues
from aea.protocols.signing.dialogues import SigningDialogue as BaseSigningDialogue
from aea.protocols.signing.dialogues import SigningDialogues as BaseSigningDialogues
from aea.skills.base import Model


from packages.fetchai.protocols.fipa.dialogues import FipaDialogue as BaseFipaDialogue
from packages.fetchai.protocols.fipa.dialogues import FipaDialogues as BaseFipaDialogues
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogue as BaseLedgerApiDialogue,
)
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)

DefaultDialogue = BaseDefaultDialogue


class DefaultDialogues(Model, BaseDefaultDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseDefaultDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return DefaultDialogue.Role.AGENT

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> DefaultDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = DefaultDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


class FipaDialogue(BaseFipaDialogue):
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
        BaseFipaDialogue.__init__(
            self, dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )
        self._terms = None  # type: Optional[Terms]
        self._associated_ledger_api_dialogue = None  # type: Optional[LedgerApiDialogue]

    @property
    def terms(self) -> Terms:
        """Get terms."""
        assert self._terms is not None, "Terms not set!"
        return self._terms

    @terms.setter
    def terms(self, terms: Terms) -> None:
        """Set terms."""
        assert self._terms is None, "Terms already set!"
        self._terms = terms

    @property
    def associated_ledger_api_dialogue(self) -> "LedgerApiDialogue":
        """Get associated_ledger_api_dialogue."""
        assert (
            self._associated_ledger_api_dialogue is not None
        ), "LedgerApiDialogue not set!"
        return self._associated_ledger_api_dialogue

    @associated_ledger_api_dialogue.setter
    def associated_ledger_api_dialogue(
        self, ledger_api_dialogue: "LedgerApiDialogue"
    ) -> None:
        """Set associated_ledger_api_dialogue"""
        assert (
            self._associated_ledger_api_dialogue is None
        ), "LedgerApiDialogue already set!"
        self._associated_ledger_api_dialogue = ledger_api_dialogue


class FipaDialogues(Model, BaseFipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseFipaDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return BaseFipaDialogue.Role.BUYER

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> FipaDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = FipaDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


class LedgerApiDialogue(BaseLedgerApiDialogue):
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
        BaseLedgerApiDialogue.__init__(
            self, dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )
        self._associated_fipa_dialogue = None  # type: Optional[FipaDialogue]

    @property
    def associated_fipa_dialogue(self) -> FipaDialogue:
        """Get associated_fipa_dialogue."""
        assert self._associated_fipa_dialogue is not None, "FipaDialogue not set!"
        return self._associated_fipa_dialogue

    @associated_fipa_dialogue.setter
    def associated_fipa_dialogue(self, fipa_dialogue: FipaDialogue) -> None:
        """Set associated_fipa_dialogue"""
        assert self._associated_fipa_dialogue is None, "FipaDialogue already set!"
        self._associated_fipa_dialogue = fipa_dialogue


class LedgerApiDialogues(Model, BaseLedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseLedgerApiDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return BaseLedgerApiDialogue.Role.AGENT

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> LedgerApiDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = LedgerApiDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


OefSearchDialogue = BaseOefSearchDialogue


class OefSearchDialogues(Model, BaseOefSearchDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseOefSearchDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return BaseOefSearchDialogue.Role.AGENT

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> OefSearchDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = OefSearchDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


class SigningDialogue(BaseSigningDialogue):
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
        BaseSigningDialogue.__init__(
            self, dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )
        self._associated_fipa_dialogue = None  # type: Optional[FipaDialogue]

    @property
    def associated_fipa_dialogue(self) -> FipaDialogue:
        """Get associated_fipa_dialogue."""
        assert self._associated_fipa_dialogue is not None, "FipaDialogue not set!"
        return self._associated_fipa_dialogue

    @associated_fipa_dialogue.setter
    def associated_fipa_dialogue(self, fipa_dialogue: FipaDialogue) -> None:
        """Set associated_fipa_dialogue"""
        assert self._associated_fipa_dialogue is None, "FipaDialogue already set!"
        self._associated_fipa_dialogue = fipa_dialogue


class SigningDialogues(Model, BaseSigningDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseSigningDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return BaseSigningDialogue.Role.SKILL

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> SigningDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = SigningDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue
```

The dialogues class stores dialogue with each AEA so we can have access to previous messages and enable us to identify possible communications problems between the `my_generic_seller` AEA and the `my_generic_buyer` AEA.

### Step 6: Update the YAML files

Since we made so many changes to our AEA we have to update the `skill.yaml` to contain our newly created scripts and the details that will be used from the strategy.

First, we update the `skill.yaml`. Make sure that your `skill.yaml` matches with the following code:

``` yaml
name: generic_buyer
author: fetchai
version: 0.5.0
description: The generic buyer skill implements the skill to purchase data.
license: Apache-2.0
aea_version: '>=0.5.0, <0.6.0'
fingerprint:
  __init__.py: QmaEDrNJBeHCJpbdFckRUhLSBqCXQ6umdipTMpYhqSKxSG
  behaviours.py: QmYfAMPG5Rnm9fGp7frZLky6cV6Z7qAhtsPNhfwtVYRuEx
  dialogues.py: QmXe9VAuinv6jgi5So7e25qgWXN16pB6tVG1iD7oAxUZ56
  handlers.py: QmX9Pphv5VkfKgYriUkzqnVBELLkpdfZd6KzEQKkCG6Da3
  strategy.py: QmP3fLkBnLyQhHngZELHeLfK59WY6Xz76bxCVm6pfE6tLh
fingerprint_ignore_patterns: []
contracts: []
protocols:
- fetchai/default:0.3.0
- fetchai/fipa:0.4.0
- fetchai/ledger_api:0.1.0
- fetchai/oef_search:0.3.0
skills: []
behaviours:
  search:
    args:
      search_interval: 5
    class_name: GenericSearchBehaviour
handlers:
  fipa:
    args: {}
    class_name: GenericFipaHandler
  ledger_api:
    args: {}
    class_name: GenericLedgerApiHandler
  oef_search:
    args: {}
    class_name: GenericOefSearchHandler
  signing:
    args: {}
    class_name: GenericSigningHandler
models:
  default_dialogues:
    args: {}
    class_name: DefaultDialogues
  fipa_dialogues:
    args: {}
    class_name: FipaDialogues
  ledger_api_dialogues:
    args: {}
    class_name: LedgerApiDialogues
  oef_search_dialogues:
    args: {}
    class_name: OefSearchDialogues
  signing_dialogues:
    args: {}
    class_name: SigningDialogues
  strategy:
    args:
      currency_id: FET
      data_model:
        attribute_one:
          is_required: true
          name: country
          type: str
        attribute_two:
          is_required: true
          name: city
          type: str
      data_model_name: location
      is_ledger_tx: true
      ledger_id: fetchai
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      search_query:
        constraint_one:
          constraint_type: ==
          search_term: country
          search_value: UK
        constraint_two:
          constraint_type: ==
          search_term: city
          search_value: Cambridge
      service_id: generic_service
    class_name: GenericStrategy
dependencies: {}
```
We must pay attention to the models and the strategy’s variables. Here we can change the price we would like to buy each reading at or the currency we would like to transact with. 

Finally, we fingerprint our new skill:

``` bash
aea fingerprint skill my_generic_buyer
```

This will hash each file and save the hash in the fingerprint. This way, in the future we can easily track if any of the files have changed.

## Run the AEAs

<!-- <details><summary>Additional steps for Raspberry Pi only!</summary>

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

</details> -->


In a separate terminal, launch a local [OEF search and communication node](../oef-ledger).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

You can run the demo either on Fetch.ai ledger or Ethereum ledger.

### Option 1: Fetch.ai ledger payment

Create the private key for the buyer AEA.

``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

#### Update the AEA configs

Both in `my_generic_seller/aea-config.yaml` and `my_generic_buyer/aea-config.yaml`, replace ```ledger_apis```: {} with the following.
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
and
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.1.0
```

#### Fund the buyer AEA

Create some wealth for your buyer on the Fetch.ai testnet. (It takes a while).

``` bash 
aea generate-wealth fetchai
```

#### Run both AEAs

Run both AEAs from their respective terminals

``` bash 
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
aea run
```
You will see that the AEAs negotiate and then transact using the Fetch.ai testnet.

### Option 2: Ethereum ledger payment

A demo to run the same scenario but with a true ledger transaction on the Ethereum Ropsten testnet. 
This demo assumes the buyer trusts our AEA to send the temperature data upon successful payment.

Create the private key for the `my_generic_buyer` AEA.

``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

#### Update the AEA configs

Both in `my_generic_seller/aea-config.yaml` and `my_generic_buyer/aea-config.yaml`, replace `ledger_apis: {}` with the following.

``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

#### Update the skill configs

In the skill `generic_seller` config (`my_generic_seller/skills/generic_seller/skill.yaml`) under strategy, amend the `currency_id` and `ledger_id` as follows.

``` yaml
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
```

In the `generic_buyer` skill config (`my_generic_buyer/skills/generic_buyer/skill.yaml`) under strategy change the `currency_id` and `ledger_id`.

``` yaml
max_buyer_tx_fee: 20000
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
```

#### Fund the generic buyer AEA

Create some wealth for your buyer on the Ethereum Ropsten test net.
Go to the <a href="https://faucet.metamask.io/"> MetaMask Faucet </a> and request some test ETH for the account your buyer AEA is using (you need to first load your AEAs private key into MetaMask). Your private key is at `my_generic_buyer/eth_private_key.txt`.

#### Run both AEAs

Run both AEAs from their respective terminals.

``` bash 
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
aea run
```

You will see that the AEAs negotiate and then transact using the Ethereum testnet.

## Delete the AEAs

When you are done, go up a level and delete the AEAs.
``` bash 
cd ..
aea delete my_generic_seller
aea delete my_generic_buyer
```

## Next steps

You have completed the "Getting Started" series. Congratulations!

### Recommended

We recommend you build your own AEA next. There are many helpful guides on here and a developer community on <a href="fetch-ai.slack.com">Slack</a>. Speak to you there!

<br />
