This guide is a step-by-step introduction to building an AEA that represents static, and dynamic data to be advertised on the <a href="../oef-ledger">Open Economic Framework</a>.

If you simply want to run the resulting AEAs <a href="../generic-skills">go here</a>.

<!-- ## Hardware Requirements (Optional)

To follow this tutorial to completion you will need:

 - Raspberry Pi 4

 - Mini SD card

 - Thermometer sensor

 - AEA Framework

The AEA will “live” inside the Raspberry Pi and will read the data from a sensor. Then it will connect to the <a href="../oef-ledger">OEF search and communication networks</a> and will identify itself as a seller of that data.

If you simply want to follow the software part of the guide then you only require the dependencies listed in the <a href="../generic-skills-step-by-step/#dependencies">Dependencies</a> section.

### Setup the environment (Optional)

You can follow the guide <a href="../raspberry-set-up"> here </a> in order to setup your environment and prepare your Raspberry Pi.

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
aea fetch fetchai/generic_seller:0.15.0
cd generic_seller
aea eject skill fetchai/generic_seller:0.17.0
cd ..
```

``` bash
aea fetch fetchai/generic_buyer:0.16.0
cd generic_buyer
aea eject skill fetchai/generic_buyer:0.17.0
cd ..
```

## Simplification step

To keep file paths consistent with the reference code, we suggest you initialize your local author as `fetchai` for the purpose of this demo only:

``` bash
aea init --reset --local --author fetchai
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

- `__init__.py`
- `behaviours.py`
- `handlers.py`
- `my_model.py`
- `skills.yaml`

### Step 2: Create the behaviour

A <a href="../api/skills/base#behaviour-objects">`Behaviour`</a> class contains the business logic specific to actions initiated by the AEA rather than reactions to other events.

Open the `behaviours.py` file (`my_generic_seller/skills/generic_seller/behaviours.py`) and add the following code (replacing the stub code already present in the file):

``` python
from typing import cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_seller.dialogues import (
    LedgerApiDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.generic_seller.strategy import GenericStrategy


DEFAULT_SERVICES_INTERVAL = 60.0
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class GenericServiceRegistrationBehaviour(TickerBehaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        services_interval = kwargs.pop(
            "services_interval", DEFAULT_SERVICES_INTERVAL
        )  # type: int
        super().__init__(tick_interval=services_interval, **kwargs)

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
            ledger_api_msg, _ = ledger_api_dialogues.create(
                counterparty=LEDGER_API_ADDRESS,
                performative=LedgerApiMessage.Performative.GET_BALANCE,
                ledger_id=strategy.ledger_id,
                address=cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
            )
            self.context.outbox.put_message(message=ledger_api_msg)
        self._register_agent()
        self._register_service()

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        pass

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self._unregister_service()
        self._unregister_agent()

    def _register_agent(self) -> None:
        """
        Register the agent's location.

        :return: None
        """
        strategy = cast(GenericStrategy, self.context.strategy)
        description = strategy.get_location_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("registering agent on SOEF.")

    def _register_service(self) -> None:
        """
        Register the agent's service.

        :return: None
        """
        strategy = cast(GenericStrategy, self.context.strategy)
        description = strategy.get_register_service_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("registering service on SOEF.")

    def _unregister_service(self) -> None:
        """
        Unregister service from the SOEF.

        :return: None
        """
        strategy = cast(GenericStrategy, self.context.strategy)
        description = strategy.get_unregister_service_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("unregistering service from SOEF.")

    def _unregister_agent(self) -> None:
        """
        Unregister agent from the SOEF.

        :return: None
        """
        strategy = cast(GenericStrategy, self.context.strategy)
        description = strategy.get_location_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("unregistering agent from SOEF.")
```

This <a href="../api/skills/behaviours#tickerbehaviour-objects">`TickerBehaviour`</a> registers and de-register our AEA’s service on the <a href="../simple-oef">SOEF search node</a> at regular tick intervals (here 60 seconds). By registering, the AEA becomes discoverable to possible clients.

The act method unregisters and registers the AEA to the <a href="../simple-oef">SOEF search node</a> on each tick. Finally, the teardown method unregisters the AEA and reports your balances.

At setup we are sending a message to the ledger connection to check the account balance for the AEA's address on the configured ledger.

### Step 3: Create the handler

So far, we have tasked the AEA with sending register/unregister requests to the <a href="../simple-oef">SOEF search node</a>. However, we have at present no way of handling the responses sent to the AEA by the <a href="../simple-oef">SOEF search node</a> or messages sent from any other AEA.

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

Let us now implement a <a href="../api/skills/base#handler-objects">`Handler`</a> to deal with the incoming messages. Open the `handlers.py` file (`my_generic_seller/skills/generic_seller/handlers.py`) and add the following code (replacing the stub code already present in the file):

``` python
from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.transaction.base import TransactionDigest
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.default.message import DefaultMessage
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


LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class GenericFipaHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[PublicId]

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
The code above is logic for handling `FipaMessages` received by the `my_generic_seller` AEA. We use `FipaDialogues` (more on this below in <a href="../generic-skills-step-by-step/#step-5-create-the-dialogues">this</a> section) to keep track of the dialogue state between the `my_generic_seller` AEA and the `my_generic_buyer` AEA.

First, we check if the message is registered to an existing dialogue or if we have to create a new dialogue. The second part matches messages with their handler based on the message's performative. We are going to implement each case in a different function.

Below the unused `teardown` function, we continue by adding the following code:

``` python
    def _handle_unidentified_dialogue(self, fipa_msg: FipaMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param fipa_msg: the message
        """
        self.context.logger.info(
            "received invalid fipa message={}, unidentified dialogue.".format(fipa_msg)
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=fipa_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": fipa_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)
```

The above code handles an unidentified dialogue by responding to the sender with a `DefaultMessage` containing the appropriate error information.

The next code block handles the `CFP` message, paste the code below the `_handle_unidentified_dialogue` function:

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
            "received CFP from sender={}".format(fipa_msg.sender[-5:])
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_matching_supply(fipa_msg.query):
            proposal, terms, data_for_sale = strategy.generate_proposal_terms_and_data(
                fipa_msg.query, fipa_msg.sender
            )
            fipa_dialogue.data_for_sale = data_for_sale
            fipa_dialogue.terms = terms
            self.context.logger.info(
                "sending a PROPOSE with proposal={} to sender={}".format(
                    proposal.values, fipa_msg.sender[-5:]
                )
            )
            proposal_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.PROPOSE,
                target_message=fipa_msg,
                proposal=proposal,
            )
            self.context.outbox.put_message(message=proposal_msg)
        else:
            self.context.logger.info(
                "declined the CFP from sender={}".format(fipa_msg.sender[-5:])
            )
            decline_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.DECLINE, target_message=fipa_msg,
            )
            self.context.outbox.put_message(message=decline_msg)
```

The above code will respond with a `PROPOSE` message to the buyer if the CFP matches the supplied services and our strategy otherwise it will respond with a `DECLINE` message.

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
            "received DECLINE from sender={}".format(fipa_msg.sender[-5:])
        )
        fipa_dialogues.dialogue_stats.add_dialogue_endstate(
            FipaDialogue.EndState.DECLINED_PROPOSE, fipa_dialogue.is_self_initiated
        )
```
If we receive a decline message from the buyer we close the dialogue and terminate this conversation with the `my_generic_buyer`.

Alternatively, we might receive an `ACCEPT` message. In order to handle this option add the following code below the `_handle_decline` function:

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
            "received ACCEPT from sender={}".format(fipa_msg.sender[-5:])
        )
        info = {"address": fipa_dialogue.terms.sender_address}
        match_accept_msg = fipa_dialogue.reply(
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            target_message=fipa_msg,
            info=info,
        )
        self.context.logger.info(
            "sending MATCH_ACCEPT_W_INFORM to sender={} with info={}".format(
                fipa_msg.sender[-5:], info,
            )
        )
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
        self.context.logger.info(
            "received INFORM from sender={}".format(fipa_msg.sender[-5:])
        )

        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_ledger_tx and "transaction_digest" in fipa_msg.info.keys():
            self.context.logger.info(
                "checking whether transaction={} has been received ...".format(
                    fipa_msg.info["transaction_digest"]
                )
            )
            ledger_api_dialogues = cast(
                LedgerApiDialogues, self.context.ledger_api_dialogues
            )
            ledger_api_msg, ledger_api_dialogue = ledger_api_dialogues.create(
                counterparty=LEDGER_API_ADDRESS,
                performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                transaction_digest=TransactionDigest(
                    fipa_dialogue.terms.ledger_id, fipa_msg.info["transaction_digest"]
                ),
            )
            ledger_api_dialogue = cast(LedgerApiDialogue, ledger_api_dialogue)
            ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
            self.context.outbox.put_message(message=ledger_api_msg)
        elif strategy.is_ledger_tx:
            self.context.logger.warning(
                "did not receive transaction digest from sender={}.".format(
                    fipa_msg.sender[-5:]
                )
            )
        elif not strategy.is_ledger_tx and "Done" in fipa_msg.info.keys():
            inform_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.INFORM,
                target_message=fipa_msg,
                info=fipa_dialogue.data_for_sale,
            )
            self.context.outbox.put_message(message=inform_msg)
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, fipa_dialogue.is_self_initiated
            )
            self.context.logger.info(
                "transaction confirmed, sending data={} to buyer={}.".format(
                    fipa_dialogue.data_for_sale, fipa_msg.sender[-5:],
                )
            )
        else:
            self.context.logger.warning(
                "did not receive transaction confirmation from sender={}.".format(
                    fipa_msg.sender[-5:]
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
            "cannot handle fipa message of performative={} in dialogue={}.".format(
                fipa_msg.performative, fipa_dialogue
            )
        )


class GenericLedgerApiHandler(Handler):
    """Implement the ledger handler."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id  # type: Optional[PublicId]

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
            self._handle_balance(ledger_api_msg)
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
            "received invalid ledger_api message={}, unidentified dialogue.".format(
                ledger_api_msg
            )
        )

    def _handle_balance(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_message: the ledger api message
        """
        self.context.logger.info(
            "starting balance on {} ledger={}.".format(
                ledger_api_msg.ledger_id, ledger_api_msg.balance,
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
            if last_message is None:
                raise ValueError("Cannot retrieve last fipa message.")
            inform_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.INFORM,
                target_message=last_message,
                info=fipa_dialogue.data_for_sale,
            )
            self.context.outbox.put_message(message=inform_msg)
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, fipa_dialogue.is_self_initiated
            )
            self.context.logger.info(
                "transaction confirmed, sending data={} to buyer={}.".format(
                    fipa_dialogue.data_for_sale, last_message.sender[-5:],
                )
            )
        else:
            self.context.logger.info(
                "transaction_receipt={} not settled or not valid, aborting".format(
                    ledger_api_msg.transaction_receipt
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
            "received ledger_api error message={} in dialogue={}.".format(
                ledger_api_msg, ledger_api_dialogue
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
            "cannot handle ledger_api message of performative={} in dialogue={}.".format(
                ledger_api_msg.performative, ledger_api_dialogue,
            )
        )


class GenericOefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

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
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
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
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_msg, oef_search_dialogue
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
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
```

The `GenericLedgerApiHandler` deals with `LedgerApiMessages` from the ledger connection. The `GenericOefSearchHandler` handles `OefSearchMessages` from the soef connection.

### Step 4: Create the strategy

Next, we are going to create the strategy that we want our `my_generic_seller` AEA to follow. Rename the `my_model.py` file (`my_generic_seller/skills/generic_seller/my_model.py`) to `strategy.py` and copy and paste the following code (replacing the stub code already present in the file):

``` python
import uuid
from typing import Any, Dict, Optional, Tuple

from aea.common import Address
from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import enforce
from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    SIMPLE_SERVICE_MODEL,
)
from aea.helpers.search.models import Description, Location, Query
from aea.helpers.transaction.base import Terms
from aea.skills.base import Model


DEFAULT_IS_LEDGER_TX = True

DEFAULT_UNIT_PRICE = 4
DEFAULT_SERVICE_ID = "generic_service"

DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SERVICE_DATA = {"key": "seller_service", "value": "generic_service"}

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
        ledger_id = kwargs.pop("ledger_id", None)
        currency_id = kwargs.pop("currency_id", None)
        self._is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)

        self._unit_price = kwargs.pop("unit_price", DEFAULT_UNIT_PRICE)
        self._service_id = kwargs.pop("service_id", DEFAULT_SERVICE_ID)

        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = {
            "location": Location(
                latitude=location["latitude"], longitude=location["longitude"]
            )
        }
        self._set_service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        enforce(
            len(self._set_service_data) == 2
            and "key" in self._set_service_data
            and "value" in self._set_service_data,
            "service_data must contain keys `key` and `value`",
        )
        self._remove_service_data = {"key": self._set_service_data["key"]}
        self._simple_service_data = {
            self._set_service_data["key"]: self._set_service_data["value"]
        }

        self._has_data_source = kwargs.pop("has_data_source", DEFAULT_HAS_DATA_SOURCE)
        data_for_sale_ordered = kwargs.pop("data_for_sale", DEFAULT_DATA_FOR_SALE)
        data_for_sale = {
            str(key): str(value) for key, value in data_for_sale_ordered.items()
        }

        super().__init__(**kwargs)
        self._ledger_id = (
            ledger_id if ledger_id is not None else self.context.default_ledger_id
        )
        if currency_id is None:
            currency_id = self.context.currency_denominations.get(self._ledger_id, None)
            enforce(
                currency_id is not None,
                f"Currency denomination for ledger_id={self._ledger_id} not specified.",
            )
        self._currency_id = currency_id
        enforce(
            self.context.agent_addresses.get(self._ledger_id, None) is not None,
            "Wallet does not contain cryptos for provided ledger id.",
        )
        self._data_for_sale = data_for_sale
```

We initialise the strategy class. We are trying to read the strategy variables from the yaml file. If this is not possible we specified some default values.

The following properties and methods deal with different aspects of the strategy. Add them under the initialization of the class:

``` python
    @property
    def data_for_sale(self) -> Dict[str, str]:
        """Get the data for sale."""
        if self._has_data_source:
            return self.collect_from_data_source()  # pragma: nocover
        return self._data_for_sale

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def is_ledger_tx(self) -> bool:
        """Check whether or not tx are settled on a ledger."""
        return self._is_ledger_tx

    def get_location_description(self) -> Description:
        """
        Get the location description.

        :return: a description of the agent's location
        """
        description = Description(
            self._agent_location, data_model=AGENT_LOCATION_MODEL,
        )
        return description

    def get_register_service_description(self) -> Description:
        """
        Get the register service description.

        :return: a description of the offered services
        """
        description = Description(
            self._set_service_data, data_model=AGENT_SET_SERVICE_MODEL,
        )
        return description

    def get_service_description(self) -> Description:
        """
        Get the simple service description.

        :return: a description of the offered services
        """
        description = Description(
            self._simple_service_data, data_model=SIMPLE_SERVICE_MODEL,
        )
        return description

    def get_unregister_service_description(self) -> Description:
        """
        Get the unregister service description.

        :return: a description of the to be removed service
        """
        description = Description(
            self._remove_service_data, data_model=AGENT_REMOVE_SERVICE_MODEL,
        )
        return description

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indiciating whether matches or not
        """
        return query.check(self.get_service_description())

    def generate_proposal_terms_and_data(  # pylint: disable=unused-argument
        self, query: Query, counterparty_address: Address
    ) -> Tuple[Description, Terms, Dict[str, str]]:
        """
        Generate a proposal matching the query.

        :param query: the query
        :param counterparty_address: the counterparty of the proposal.
        :return: a tuple of proposal, terms and the weather data
        """
        data_for_sale = self.data_for_sale
        sale_quantity = len(data_for_sale)
        seller_address = self.context.agent_addresses[self.ledger_id]
        total_price = sale_quantity * self._unit_price
        if self.is_ledger_tx:
            tx_nonce = LedgerApis.generate_tx_nonce(
                identifier=self.ledger_id,
                seller=seller_address,
                client=counterparty_address,
            )
        else:
            tx_nonce = uuid.uuid4().hex  # pragma: nocover
        proposal = Description(
            {
                "ledger_id": self.ledger_id,
                "price": total_price,
                "currency_id": self._currency_id,
                "service_id": self._service_id,
                "quantity": sale_quantity,
                "tx_nonce": tx_nonce,
            }
        )
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=seller_address,
            counterparty_address=counterparty_address,
            amount_by_currency_id={self._currency_id: total_price},
            quantities_by_good_id={self._service_id: -sale_quantity},
            is_sender_payable_tx_fee=False,
            nonce=tx_nonce,
            fee_by_currency_id={self._currency_id: 0},
        )
        return proposal, terms, data_for_sale

    def collect_from_data_source(self) -> Dict[str, str]:
        """Implement the logic to communicate with the sensor."""
        raise NotImplementedError
```

Before the creation of the actual proposal, we have to check if the sale generates value for us or a loss. If it is a loss, we abort and warn the developer. The helper private function `collect_from_data_source`, is where we read data from our sensor or in case we do not have a sensor use some default data provided.

### Step 5: Create the dialogues

When we are negotiating with other AEAs we would like to keep track of the state of these negotiations. To this end we create a new file in the skill folder (`my_generic_seller/skills/generic_seller/`) and name it `dialogues.py`. Inside this file add the following code:

``` python
from typing import Dict, Optional, Type

from aea.common import Address
from aea.exceptions import AEAEnforceError, enforce
from aea.helpers.transaction.base import Terms
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.skills.base import Model

from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogue as BaseDefaultDialogue,
)
from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogues as BaseDefaultDialogues,
)
from packages.fetchai.protocols.fipa.dialogues import FipaDialogue as BaseFipaDialogue
from packages.fetchai.protocols.fipa.dialogues import FipaDialogues as BaseFipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogue as BaseLedgerApiDialogue,
)
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
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

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return DefaultDialogue.Role.AGENT

        BaseDefaultDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
        )


class FipaDialogue(BaseFipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
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
        BaseFipaDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self.data_for_sale = None  # type: Optional[Dict[str, str]]
        self._terms = None  # type: Optional[Terms]

    @property
    def terms(self) -> Terms:
        """Get terms."""
        if self._terms is None:
            raise AEAEnforceError("Terms not set!")
        return self._terms

    @terms.setter
    def terms(self, terms: Terms) -> None:
        """Set terms."""
        enforce(self._terms is None, "Terms already set!")
        self._terms = terms


class FipaDialogues(Model, BaseFipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return FipaDialogue.Role.SELLER

        BaseFipaDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=FipaDialogue,
        )


class LedgerApiDialogue(BaseLedgerApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[LedgerApiMessage] = LedgerApiMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        BaseLedgerApiDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._associated_fipa_dialogue = None  # type: Optional[FipaDialogue]

    @property
    def associated_fipa_dialogue(self) -> FipaDialogue:
        """Get associated_fipa_dialogue."""
        if self._associated_fipa_dialogue is None:
            raise AEAEnforceError("FipaDialogue not set!")
        return self._associated_fipa_dialogue

    @associated_fipa_dialogue.setter
    def associated_fipa_dialogue(self, fipa_dialogue: FipaDialogue) -> None:
        """Set associated_fipa_dialogue"""
        enforce(self._associated_fipa_dialogue is None, "FipaDialogue already set!")
        self._associated_fipa_dialogue = fipa_dialogue


class LedgerApiDialogues(Model, BaseLedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseLedgerApiDialogue.Role.AGENT

        BaseLedgerApiDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=LedgerApiDialogue,
        )


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

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseOefSearchDialogue.Role.AGENT

        BaseOefSearchDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
        )
```

The `FipaDialogues` class stores dialogue with each `my_generic_buyer` (and other AEAs) and exposes a number of helpful methods to manage them. This helps us match messages to a dialogue, access previous messages and enable us to identify possible communications problems between the `my_generic_seller` AEA and the `my_generic_buyer` AEA. It also keeps track of the data that we offer for sale during the proposal phase.

The `FipaDialogues` class extends `BaseFipaDialogues`, which itself derives from the base <a href="../api/helpers/dialogue/base#dialogues-objects">`Dialogues`</a> class. Similarly, the `FipaDialogue` class extends `BaseFipaDialogue`, which itself derives from the base <a href="../api/helpers/dialogue/base#dialogue-objects">`Dialogue`</a> class. To learn more about dialogues have a look <a href="../protocol">here</a>.

### Step 6: Update the YAML files

Since we made so many changes to our AEA we have to update the `skill.yaml` (at `my_generic_seller/skills/generic_seller/skill.yaml`). Make sure that your `skill.yaml` matches with the following code

``` yaml
name: generic_seller
author: fetchai
version: 0.1.0
type: skill
description: The weather station skill implements the functionality to sell weather
  data.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
fingerprint:
  __init__.py: QmNkZAetyctaZCUf6ACxP5onGWsSxu2hjSNoFmJ3ta6Lta
  behaviours.py: QmcFahpL4DZ1rsTNEK1BT3e5T8TEJJg2hP4ytkzdqKuJnZ
  dialogues.py: QmRmoFp9xi1p1THVBYym9xEwW88KgkBHgz45LgrYbBecQw
  handlers.py: QmT4nvKikWXfGAEdRS8Qn8w89Gbh5zPb4EDB6EwPVP2YDJ
  strategy.py: QmP69kCtcovLD2Z7quESuNxVEyNuiZgqqbwozp6wAbvBCd
fingerprint_ignore_patterns: []
contracts: []
protocols:
- fetchai/default:0.9.0
- fetchai/fipa:0.10.0
- fetchai/ledger_api:0.7.0
- fetchai/oef_search:0.10.0
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
      has_data_source: false
      is_ledger_tx: true
      ledger_id: fetchai
      location:
        latitude: 51.5194
        longitude: 0.127
      service_data:
        key: seller_service
        value: generic_service
      service_id: generic_service
      unit_price: 10
    class_name: GenericStrategy
dependencies: {}
```

We must pay attention to the models and in particular the strategy’s variables. Here we can change the price we would like to sell each reading for or the currency we would like to transact with. Lastly, the dependencies are the third party packages we need to install in order to get readings from the sensor.

Finally, we fingerprint our new skill:

``` bash
aea fingerprint skill fetchai/generic_seller:0.1.0
```

This will hash each file and save the hash in the fingerprint. This way, in the future we can easily track if any of the files have changed.


## Generic Buyer AEA

### Step 1: Create the AEA

In a new terminal, create a new AEA by typing the following command in the terminal:

``` bash
aea create my_generic_buyer
cd my_generic_buyer
```

Our newly created AEA is inside the current working directory. Let’s create our new skill that will handle the purchase of the data. Type the following command:

``` bash
aea scaffold skill generic_buyer
```

This command will create the correct structure for a new skill inside our AEA project You can locate the newly created skill inside the skills folder (`my_generic_buyer/skills/generic_buyer/`) and it must contain the following files:

- `__init__.py`
- `behaviours.py`
- `handlers.py`
- `my_model.py`
- `skills.yaml`

### Step 2: Create the behaviour

A <a href="../api/skills/base#behaviour-objects">`Behaviour`</a> class contains the business logic specific to actions initiated by the AEA rather than reactions to other events.

Open the `behaviours.py` (`my_generic_buyer/skills/generic_buyer/behaviours.py`) and add the following code (replacing the stub code already present in the file):

``` python
from typing import cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.dialogues import (
    LedgerApiDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy


DEFAULT_SEARCH_INTERVAL = 5.0
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


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
            ledger_api_msg, _ = ledger_api_dialogues.create(
                counterparty=LEDGER_API_ADDRESS,
                performative=LedgerApiMessage.Performative.GET_BALANCE,
                ledger_id=strategy.ledger_id,
                address=cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
            )
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
            query = strategy.get_location_and_service_query()
            oef_search_dialogues = cast(
                OefSearchDialogues, self.context.oef_search_dialogues
            )
            oef_search_msg, _ = oef_search_dialogues.create(
                counterparty=self.context.search_service_address,
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=query,
            )
            self.context.outbox.put_message(message=oef_search_msg)

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
```

This <a href="../api/skills/behaviours#tickerbehaviour-objects">`TickerBehaviour`</a> will search on  the <a href="../simple-oef">SOEF search node</a> with a specific query at regular tick intervals.

### Step 3: Create the handler

So far, we have tasked the AEA with sending search queries to the <a href="../simple-oef">SOEF search node</a>. However, we have at present no way of handling the responses sent to the AEA by the <a href="../simple-oef">SOEF search node</a> or messages sent by other agent.

Let us now implement a <a href="../api/skills/base#handler-objects">`Handler`</a> to deal with the incoming messages. Open the `handlers.py` file (`my_generic_buyer/skills/generic_buyer/handlers.py`) and add the following code (replacing the stub code already present in the file):

``` python
import pprint
from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.signing.message import SigningMessage
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


LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class GenericFipaHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[PublicId]

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
            "received invalid fipa message={}, unidentified dialogue.".format(fipa_msg)
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=fipa_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": fipa_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)
```
The above code handles the unidentified dialogues. And responds with an error message to the sender. Next we will handle the `PROPOSE` message that we receive from the `my_generic_seller` AEA:

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
            "received proposal={} from sender={}".format(
                fipa_msg.proposal.values, fipa_msg.sender[-5:],
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        acceptable = strategy.is_acceptable_proposal(fipa_msg.proposal)
        affordable = strategy.is_affordable_proposal(fipa_msg.proposal)
        if acceptable and affordable:
            self.context.logger.info(
                "accepting the proposal from sender={}".format(fipa_msg.sender[-5:])
            )
            terms = strategy.terms_from_proposal(fipa_msg.proposal, fipa_msg.sender)
            fipa_dialogue.terms = terms
            accept_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.ACCEPT, target_message=fipa_msg,
            )
            self.context.outbox.put_message(message=accept_msg)
        else:
            self.context.logger.info(
                "declining the proposal from sender={}".format(fipa_msg.sender[-5:])
            )
            decline_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.DECLINE, target_message=fipa_msg,
            )
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
            "received DECLINE from sender={}".format(fipa_msg.sender[-5:])
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
            "received MATCH_ACCEPT_W_INFORM from sender={} with info={}".format(
                fipa_msg.sender[-5:], fipa_msg.info
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_ledger_tx:
            transfer_address = fipa_msg.info.get("address", None)
            if transfer_address is not None and isinstance(transfer_address, str):
                fipa_dialogue.terms.counterparty_address = (  # pragma: nocover
                    transfer_address
                )
            ledger_api_dialogues = cast(
                LedgerApiDialogues, self.context.ledger_api_dialogues
            )
            ledger_api_msg, ledger_api_dialogue = ledger_api_dialogues.create(
                counterparty=LEDGER_API_ADDRESS,
                performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
                terms=fipa_dialogue.terms,
            )
            ledger_api_dialogue = cast(LedgerApiDialogue, ledger_api_dialogue)
            ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
            fipa_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
            self.context.outbox.put_message(message=ledger_api_msg)
            self.context.logger.info(
                "requesting transfer transaction from ledger api..."
            )
        else:
            inform_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.INFORM,
                target_message=fipa_msg,
                info={"Done": "Sending payment via bank transfer"},
            )
            self.context.outbox.put_message(message=inform_msg)
            self.context.logger.info(
                "informing counterparty={} of payment.".format(fipa_msg.sender[-5:])
            )
```
The first thing we are checking is if we enabled our AEA to transact with a ledger. If we can transact with a ledger we generate a `LedgerApiMessage` of performative `GET_RAW_TRANSACTION` and send it to the ledger connection. The ledger connection will construct a raw transaction for us, using the relevant ledger api.

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
            "received INFORM from sender={}".format(fipa_msg.sender[-5:])
        )
        if len(fipa_msg.info.keys()) >= 1:
            data = fipa_msg.info
            self.context.logger.info(
                "received the following data={}".format(pprint.pformat(data))
            )
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, fipa_dialogue.is_self_initiated
            )
            strategy = cast(GenericStrategy, self.context.strategy)
            strategy.successful_trade_with_counterparty(fipa_msg.sender, data)
        else:
            self.context.logger.info(
                "received no data from sender={}".format(fipa_msg.sender[-5:])
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
            "cannot handle fipa message of performative={} in dialogue={}.".format(
                fipa_msg.performative, fipa_dialogue
            )
        )
```
The main difference between the `generic_buyer` and the `generic_seller` skill `handlers.py` file is that in this one we create more than one handler.

The reason is that we receive messages not only from the `my_generic_seller` AEA but also from the `DecisionMaker` and the <a href="../simple-oef">SOEF search node</a>. We need one handler for each type of protocol we use.

To handle the messages in the `oef_search` protocol used by the <a href="../simple-oef">SOEF search node</a> we add the following code in the same file (`my_generic_buyer/skills/generic_buyer/handlers.py`):

``` python
class GenericOefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

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
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
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
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_msg, oef_search_dialogue
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
                f"found no agents in dialogue={oef_search_dialogue}, continue searching."
            )
            return
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_stop_searching_on_result:
            self.context.logger.info(
                "found agents={}, stopping search.".format(
                    list(map(lambda x: x[-5:], oef_search_msg.agents)),
                )
            )
            strategy.is_searching = False  # stopping search
        else:
            self.context.logger.info(
                "found agents={}.".format(
                    list(map(lambda x: x[-5:], oef_search_msg.agents)),
                )
            )
        query = strategy.get_service_query()
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        counterparties = strategy.get_acceptable_counterparties(oef_search_msg.agents)
        for counterparty in counterparties:
            cfp_msg, _ = fipa_dialogues.create(
                counterparty=counterparty,
                performative=FipaMessage.Performative.CFP,
                query=query,
            )
            self.context.outbox.put_message(message=cfp_msg)
            self.context.logger.info(
                "sending CFP to agent={}".format(counterparty[-5:])
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
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
```
When we receive a message from the <a href="../simple-oef">SOEF search node</a> of a type `OefSearchMessage.Performative.SEARCH_RESULT`, we are passing the details to the relevant handler method. In the `_handle_search` function we are checking that the response contains some agents and we stop the search if it does. We pick our first agent and we send a `CFP` message.

The last handlers we need are the `GenericSigningHandler` and the `GenericLedgerApiHandler`. This handler will handle the `SigningMessages` that we receive from the `DecisionMaker`. The `GenericLedgerApiHandler` will handle the `LedgerApiMessages` that we receive from the ledger connection.

``` python
class GenericSigningHandler(Handler):
    """Implement the signing handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[PublicId]

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
            "received invalid signing message={}, unidentified dialogue.".format(
                signing_msg
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
        self.context.logger.info("transaction signing was successful.")
        fipa_dialogue = signing_dialogue.associated_fipa_dialogue
        ledger_api_dialogue = fipa_dialogue.associated_ledger_api_dialogue
        last_ledger_api_msg = ledger_api_dialogue.last_incoming_message
        if last_ledger_api_msg is None:
            raise ValueError("Could not retrieve last message in ledger api dialogue")
        ledger_api_msg = ledger_api_dialogue.reply(
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            target_message=last_ledger_api_msg,
            signed_transaction=signing_msg.signed_transaction,
        )
        self.context.outbox.put_message(message=ledger_api_msg)
        self.context.logger.info("sending transaction to ledger.")

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
            "transaction signing was not successful. Error_code={} in dialogue={}".format(
                signing_msg.error_code, signing_dialogue
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
            "cannot handle signing message of performative={} in dialogue={}.".format(
                signing_msg.performative, signing_dialogue
            )
        )


class GenericLedgerApiHandler(Handler):
    """Implement the ledger handler."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id  # type: Optional[PublicId]

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
            self._handle_balance(ledger_api_msg)
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
            "received invalid ledger_api message={}, unidentified dialogue.".format(
                ledger_api_msg
            )
        )

    def _handle_balance(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_message: the ledger api message
        """
        strategy = cast(GenericStrategy, self.context.strategy)
        if ledger_api_msg.balance > 0:
            self.context.logger.info(
                "starting balance on {} ledger={}.".format(
                    strategy.ledger_id, ledger_api_msg.balance,
                )
            )
            strategy.balance = ledger_api_msg.balance
            strategy.is_searching = True
        else:
            self.context.logger.warning(
                "you have no starting balance on {} ledger!".format(strategy.ledger_id)
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
        self.context.logger.info("received raw transaction={}".format(ledger_api_msg))
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            raw_transaction=ledger_api_msg.raw_transaction,
            terms=ledger_api_dialogue.associated_fipa_dialogue.terms,
        )
        signing_dialogue = cast(SigningDialogue, signing_dialogue)
        signing_dialogue.associated_fipa_dialogue = (
            ledger_api_dialogue.associated_fipa_dialogue
        )
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "proposing the transaction to the decision maker. Waiting for confirmation ..."
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
            "transaction was successfully submitted. Transaction digest={}".format(
                ledger_api_msg.transaction_digest
            )
        )
        fipa_msg = cast(Optional[FipaMessage], fipa_dialogue.last_incoming_message)
        if fipa_msg is None:
            raise ValueError("Could not retrieve fipa message")
        inform_msg = fipa_dialogue.reply(
            performative=FipaMessage.Performative.INFORM,
            target_message=fipa_msg,
            info={"transaction_digest": ledger_api_msg.transaction_digest.body},
        )
        self.context.outbox.put_message(message=inform_msg)
        self.context.logger.info(
            "informing counterparty={} of transaction digest.".format(
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
            "received ledger_api error message={} in dialogue={}.".format(
                ledger_api_msg, ledger_api_dialogue
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
            "cannot handle ledger_api message of performative={} in dialogue={}.".format(
                ledger_api_msg.performative, ledger_api_dialogue,
            )
        )
```

### Step 4: Create the strategy

We are going to create the strategy that we want our AEA to follow. Rename the `my_model.py` file (in `my_generic_buyer/skills/generic_buyer/`) to `strategy.py` and paste the following code (replacing the stub code already present in the file):

``` python
from aea.common import Address
from aea.exceptions import enforce
from aea.helpers.search.generic import SIMPLE_SERVICE_MODEL
from aea.helpers.search.models import (
    Constraint,
    ConstraintType,
    Description,
    Location,
    Query,
)
from aea.helpers.transaction.base import Terms
from aea.skills.base import Model


DEFAULT_IS_LEDGER_TX = True

DEFAULT_MAX_UNIT_PRICE = 5
DEFAULT_MAX_TX_FEE = 2
DEFAULT_SERVICE_ID = "generic_service"

DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SEARCH_QUERY = {
    "search_key": "seller_service",
    "search_value": "generic_service",
    "constraint_type": "==",
}
DEFAULT_SEARCH_RADIUS = 5.0

DEFAULT_MAX_NEGOTIATIONS = 2


class GenericStrategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        ledger_id = kwargs.pop("ledger_id", None)
        currency_id = kwargs.pop("currency_id", None)
        self._is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)

        self._max_unit_price = kwargs.pop("max_unit_price", DEFAULT_MAX_UNIT_PRICE)
        self._max_tx_fee = kwargs.pop("max_tx_fee", DEFAULT_MAX_TX_FEE)
        self._service_id = kwargs.pop("service_id", DEFAULT_SERVICE_ID)

        self._search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = Location(
            latitude=location["latitude"], longitude=location["longitude"]
        )
        self._radius = kwargs.pop("search_radius", DEFAULT_SEARCH_RADIUS)

        self._max_negotiations = kwargs.pop(
            "max_negotiations", DEFAULT_MAX_NEGOTIATIONS
        )
        self._is_stop_searching_on_result = kwargs.pop("stop_searching_on_result", True)

        super().__init__(**kwargs)
        self._ledger_id = (
            ledger_id if ledger_id is not None else self.context.default_ledger_id
        )
        if currency_id is None:
            currency_id = self.context.currency_denominations.get(self._ledger_id, None)
            enforce(
                currency_id is not None,
                f"Currency denomination for ledger_id={self._ledger_id} not specified.",
            )
        self._currency_id = currency_id
        self._is_searching = False
        self._balance = 0
```

We initialize the strategy class by trying to read the strategy variables from the YAML file. If this is not possible we specified some default values. The following two methods are related to the oef search service, add them under the initialization of the class:

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
    def is_stop_searching_on_result(self) -> bool:
        """Check if search is stopped on result."""
        return self._is_stop_searching_on_result

    @property
    def is_searching(self) -> bool:
        """Check if the agent is searching."""
        return self._is_searching

    @is_searching.setter
    def is_searching(self, is_searching: bool) -> None:
        """Check if the agent is searching."""
        enforce(isinstance(is_searching, bool), "Can only set bool on is_searching!")
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

    def get_location_and_service_query(self) -> Query:
        """
        Get the location and service query of the agent.

        :return: the query
        """
        close_to_my_service = Constraint(
            "location", ConstraintType("distance", (self._agent_location, self._radius))
        )
        service_key_filter = Constraint(
            self._search_query["search_key"],
            ConstraintType(
                self._search_query["constraint_type"],
                self._search_query["search_value"],
            ),
        )
        query = Query([close_to_my_service, service_key_filter],)
        return query

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        service_key_filter = Constraint(
            self._search_query["search_key"],
            ConstraintType(
                self._search_query["constraint_type"],
                self._search_query["search_value"],
            ),
        )
        query = Query([service_key_filter], model=SIMPLE_SERVICE_MODEL)
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

    def get_acceptable_counterparties(
        self, counterparties: Tuple[str, ...]
    ) -> Tuple[str, ...]:
        """
        Process counterparties and drop unacceptable ones.

        :return: list of counterparties
        """
        valid_counterparties: List[str] = []
        for idx, counterparty in enumerate(counterparties):
            if idx < self.max_negotiations:
                valid_counterparties.append(counterparty)
        return tuple(valid_counterparties)

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

    def successful_trade_with_counterparty(
        self, counterparty: str, data: Dict[str, str]
    ) -> None:
        """
        Do something on successful trade.

        :param counterparty: the counterparty address
        :param data: the data
        :return: False
        """
        pass
```

### Step 5: Create the dialogues

As mentioned, when we are negotiating with other AEA we would like to keep track of these negotiations for various reasons. Create a new file and name it `dialogues.py` (in `my_generic_buyer/skills/generic_buyer/`). Inside this file add the following code:

``` python
from typing import Optional, Type

from aea.common import Address
from aea.exceptions import AEAEnforceError, enforce
from aea.helpers.transaction.base import Terms
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.skills.base import Model

from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogue as BaseDefaultDialogue,
)
from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogues as BaseDefaultDialogues,
)
from packages.fetchai.protocols.fipa.dialogues import FipaDialogue as BaseFipaDialogue
from packages.fetchai.protocols.fipa.dialogues import FipaDialogues as BaseFipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogue as BaseLedgerApiDialogue,
)
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogue as BaseSigningDialogue,
)
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.fetchai.protocols.signing.message import SigningMessage


DefaultDialogue = BaseDefaultDialogue


class DefaultDialogues(Model, BaseDefaultDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return DefaultDialogue.Role.AGENT

        BaseDefaultDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
        )


class FipaDialogue(BaseFipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
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
        BaseFipaDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._terms = None  # type: Optional[Terms]
        self._associated_ledger_api_dialogue = None  # type: Optional[LedgerApiDialogue]

    @property
    def terms(self) -> Terms:
        """Get terms."""
        if self._terms is None:
            raise AEAEnforceError("Terms not set!")
        return self._terms

    @terms.setter
    def terms(self, terms: Terms) -> None:
        """Set terms."""
        enforce(self._terms is None, "Terms already set!")
        self._terms = terms

    @property
    def associated_ledger_api_dialogue(self) -> "LedgerApiDialogue":
        """Get associated_ledger_api_dialogue."""
        if self._associated_ledger_api_dialogue is None:
            raise AEAEnforceError("LedgerApiDialogue not set!")
        return self._associated_ledger_api_dialogue

    @associated_ledger_api_dialogue.setter
    def associated_ledger_api_dialogue(
        self, ledger_api_dialogue: "LedgerApiDialogue"
    ) -> None:
        """Set associated_ledger_api_dialogue"""
        enforce(
            self._associated_ledger_api_dialogue is None,
            "LedgerApiDialogue already set!",
        )
        self._associated_ledger_api_dialogue = ledger_api_dialogue


class FipaDialogues(Model, BaseFipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseFipaDialogue.Role.BUYER

        BaseFipaDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=FipaDialogue,
        )


class LedgerApiDialogue(BaseLedgerApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[LedgerApiMessage] = LedgerApiMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        BaseLedgerApiDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._associated_fipa_dialogue = None  # type: Optional[FipaDialogue]

    @property
    def associated_fipa_dialogue(self) -> FipaDialogue:
        """Get associated_fipa_dialogue."""
        if self._associated_fipa_dialogue is None:
            raise AEAEnforceError("FipaDialogue not set!")
        return self._associated_fipa_dialogue

    @associated_fipa_dialogue.setter
    def associated_fipa_dialogue(self, fipa_dialogue: FipaDialogue) -> None:
        """Set associated_fipa_dialogue"""
        enforce(self._associated_fipa_dialogue is None, "FipaDialogue already set!")
        self._associated_fipa_dialogue = fipa_dialogue


class LedgerApiDialogues(Model, BaseLedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseLedgerApiDialogue.Role.AGENT

        BaseLedgerApiDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=LedgerApiDialogue,
        )


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

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseOefSearchDialogue.Role.AGENT

        BaseOefSearchDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
        )


class SigningDialogue(BaseSigningDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[SigningMessage] = SigningMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        BaseSigningDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._associated_fipa_dialogue = None  # type: Optional[FipaDialogue]

    @property
    def associated_fipa_dialogue(self) -> FipaDialogue:
        """Get associated_fipa_dialogue."""
        if self._associated_fipa_dialogue is None:
            raise AEAEnforceError("FipaDialogue not set!")
        return self._associated_fipa_dialogue

    @associated_fipa_dialogue.setter
    def associated_fipa_dialogue(self, fipa_dialogue: FipaDialogue) -> None:
        """Set associated_fipa_dialogue"""
        enforce(self._associated_fipa_dialogue is None, "FipaDialogue already set!")
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

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseSigningDialogue.Role.SKILL

        BaseSigningDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=SigningDialogue,
        )
```

The dialogues class stores dialogue with each AEA and other AEA components so we can have access to previous messages and enable us to identify possible communications problems between the `my_generic_seller` AEA and the `my_generic_buyer` AEA.

### Step 6: Update the YAML files

Since we made so many changes to our AEA we have to update the `skill.yaml` to contain our newly created scripts and the details that will be used from the strategy.

First, we update the `skill.yaml`. Make sure that your `skill.yaml` matches with the following code:

``` yaml
name: generic_buyer
author: fetchai
version: 0.1.0
type: skill
description: The weather client skill implements the skill to purchase weather data.
license: Apache-2.0
aea_version: '>=0.7.0, <0.8.0'
fingerprint:
  __init__.py: QmNkZAetyctaZCUf6ACxP5onGWsSxu2hjSNoFmJ3ta6Lta
  behaviours.py: QmUBQvZkoCcik71vqRZGP4JJBgFP2kj8o7C24dfkAphitP
  dialogues.py: Qmf3McwyT5wMv3BzoN1L3ssqZzEq19LShEjQueiKqvADcX
  handlers.py: QmQVmi3GnuYJ5VM4trYjUeJyFHVfrUeMGDsRmtNCuntKA8
  strategy.py: QmQHQsjAsPiox5zMtMHhdhhhHt4rKq3cs3bqnwjgGSFp6n
fingerprint_ignore_patterns: []
contracts: []
protocols:
- fetchai/default:0.9.0
- fetchai/fipa:0.10.0
- fetchai/ledger_api:0.7.0
- fetchai/oef_search:0.10.0
- fetchai/signing:0.7.0
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
      is_ledger_tx: true
      ledger_id: fetchai
      location:
        latitude: 51.5194
        longitude: 0.127
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      search_query:
        constraint_type: ==
        search_key: seller_service
        search_value: generic_service
      search_radius: 5.0
      service_id: generic_service
    class_name: GenericStrategy
dependencies: {}
```
We must pay attention to the models and the strategy’s variables. Here we can change the price we would like to buy each reading at or the currency we would like to transact with.

Finally, we fingerprint our new skill:

``` bash
aea fingerprint skill fetchai/generic_buyer:0.1.0
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
and replace it with your IP (the IP of the machine that runs the <a href="../oef-ledger">OEF search and communication node</a> image.)

</details> -->

### Create private keys

Create the private key for each AEA:

``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
```

### Update the AEA configs

Both in `my_generic_seller/aea-config.yaml` and `my_generic_buyer/aea-config.yaml`, and
``` yaml
default_routing:
  fetchai/ledger_api:0.7.0: fetchai/ledger:0.10.0
  fetchai/oef_search:0.10.0: fetchai/soef:0.13.0
```

### Fund the buyer AEA

Create some wealth for your buyer on the Fetch.ai testnet. (It takes a while).

``` bash
aea generate-wealth fetchai --sync
```

### Run seller AEA

Add the remaining packages for the seller AEA, then run it:

``` bash
aea add connection fetchai/p2p_libp2p:0.12.0
aea add connection fetchai/soef:0.13.0
aea add connection fetchai/ledger:0.10.0
aea add protocol fetchai/fipa:0.10.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.12.0
aea run
```

Once you see a message of the form `To join its network use multiaddr: ['SOME_ADDRESS']` take note of the address.

#### Run buyer AEA

Add the remaining packages for the buyer AEA:

``` bash
aea add connection fetchai/p2p_libp2p:0.12.0
aea add connection fetchai/soef:0.13.0
aea add connection fetchai/ledger:0.10.0
aea add protocol fetchai/fipa:0.10.0
aea add protocol fetchai/signing:0.7.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.12.0
```

Then, update the configuration of the buyer AEA's p2p connection (in `vendor/fetchai/connections/p2p_libp2p/connection.yaml`) replace the following:

``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```

where `SOME_ADDRESS` is replaced accordingly.

Then run the buyer AEA:
``` bash
aea run
```

You will see that the AEAs negotiate and then transact using the Agentland testnet.

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

We recommend you build your own AEA next. There are many helpful guides on here and a developer community on <a href="https://fetch-ai.slack.com" target="_blank">Slack</a>. Speak to you there!

<br />