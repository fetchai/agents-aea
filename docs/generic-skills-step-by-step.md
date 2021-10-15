This guide is a step-by-step introduction to building AEAs that advertise their static and dynamic data, find other AEAs with required data, negotiate terms of trade, and carry out trades via ledger transactions.

If you simply want to run the resulting AEAs <a href="../generic-skills">go here</a>.

## Dependencies (Required)

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Reference code (Optional)

This step-by-step guide goes through the creation of two AEAs which are already developed by Fetch.ai. You can get the finished AEAs, and compare your code against them, by following the next steps:

``` bash
aea fetch fetchai/generic_seller:0.28.0
cd generic_seller
aea eject skill fetchai/generic_seller:0.27.0
cd ..
```

``` bash
aea fetch fetchai/generic_buyer:0.29.0
cd generic_buyer
aea eject skill fetchai/generic_buyer:0.26.0
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
aea install
```
Our newly created AEA is inside the current working directory. Let’s create our new skill that will handle the sale of data. Type the following command:
``` bash
aea scaffold skill generic_seller
```

The `scaffold skill` command creates the correct structure for a new skill inside our AEA project. You can locate the newly created skill under the "skills" folder (`my_generic_seller/skills/generic_seller/`), and it must contain the following files:

- `__init__.py`
- `behaviours.py`
- `handlers.py`
- `my_model.py`
- `skills.yaml`

### Step 2: Create the behaviour

A <a href="../api/skills/base#behaviour-objects">`Behaviour`</a> class contains the business logic specific to actions initiated by the AEA, rather than reactions to other events.

Open the `behaviours.py` file (`my_generic_seller/skills/generic_seller/behaviours.py`) and replace the stub code with the following:

``` python
from typing import Any, Optional, cast

from aea.helpers.search.models import Description
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
DEFAULT_MAX_SOEF_REGISTRATION_RETRIES = 5
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class GenericServiceRegistrationBehaviour(TickerBehaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs: Any):
        """Initialise the behaviour."""
        services_interval = kwargs.pop(
            "services_interval", DEFAULT_SERVICES_INTERVAL
        )  # type: int
        self._max_soef_registration_retries = kwargs.pop(
            "max_soef_registration_retries", DEFAULT_MAX_SOEF_REGISTRATION_RETRIES
        )  # type: int
        super().__init__(tick_interval=services_interval, **kwargs)

        self.failed_registration_msg = None  # type: Optional[OefSearchMessage]
        self._nb_retries = 0

    def setup(self) -> None:
        """Implement the setup."""
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

    def act(self) -> None:
        """Implement the act."""
        self._retry_failed_registration()

    def teardown(self) -> None:
        """Implement the task teardown."""
        self._unregister_service()
        self._unregister_agent()

    def _retry_failed_registration(self) -> None:
        """Retry a failed registration."""
        if self.failed_registration_msg is not None:
            self._nb_retries += 1
            if self._nb_retries > self._max_soef_registration_retries:
                self.context.is_active = False
                return

            oef_search_dialogues = cast(
                OefSearchDialogues, self.context.oef_search_dialogues
            )
            oef_search_msg, _ = oef_search_dialogues.create(
                counterparty=self.failed_registration_msg.to,
                performative=self.failed_registration_msg.performative,
                service_description=self.failed_registration_msg.service_description,
            )
            self.context.outbox.put_message(message=oef_search_msg)
            self.context.logger.info(
                f"Retrying registration on SOEF. Retry {self._nb_retries} out of {self._max_soef_registration_retries}."
            )

            self.failed_registration_msg = None

    def _register(self, description: Description, logger_msg: str) -> None:
        """
        Register something on the SOEF.

        :param description: the description of what is being registered
        :param logger_msg: the logger message to print after the registration
        """
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info(logger_msg)

    def _register_agent(self) -> None:
        """Register the agent's location."""
        strategy = cast(GenericStrategy, self.context.strategy)
        description = strategy.get_location_description()
        self._register(description, "registering agent on SOEF.")

    def register_service(self) -> None:
        """Register the agent's service."""
        strategy = cast(GenericStrategy, self.context.strategy)
        description = strategy.get_register_service_description()
        self._register(description, "registering agent's service on the SOEF.")

    def register_genus(self) -> None:
        """Register the agent's personality genus."""
        strategy = cast(GenericStrategy, self.context.strategy)
        description = strategy.get_register_personality_description()
        self._register(
            description, "registering agent's personality genus on the SOEF."
        )

    def register_classification(self) -> None:
        """Register the agent's personality classification."""
        strategy = cast(GenericStrategy, self.context.strategy)
        description = strategy.get_register_classification_description()
        self._register(
            description, "registering agent's personality classification on the SOEF."
        )

    def _unregister_service(self) -> None:
        """Unregister service from the SOEF."""
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
        """Unregister agent from the SOEF."""
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

This <a href="../api/skills/behaviours#tickerbehaviour-objects">`TickerBehaviour`</a> registers (see `setup` method) and deregisters (see `teardown` method) our AEA’s service on the <a href="../simple-oef">SOEF search node</a> at regular tick intervals (here 60 seconds). By registering, the AEA becomes discoverable to other AEAs.

In `setup`, prior to registrations, we send a message to the ledger connection to check the account balance for the AEA's address on the configured ledger.

### Step 3: Create the handler

So far, we have tasked the AEA with sending register/unregister requests to the <a href="../simple-oef">SOEF search node</a>. However at present, the AEA has no way of handling the responses it receives from the search node, or in fact messages sent by any other AEA.

We have to specify the logic to negotiate with another AEA based on the strategy we want our AEA to follow. The following diagram illustrates the negotiation flow that we want this AEA to use, as well as interactions with a search node and the blockchain between a `seller_AEA` and a `buyer_AEA`.

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

In our case, `my_generic_seller` is the `Seller_AEA` in the above figure.

Let us now implement a <a href="../api/skills/base#handler-objects">`Handler`</a> to deal with incoming messages. Open the `handlers.py` file (`my_generic_seller/skills/generic_seller/handlers.py`) and replace the stub code with the following:

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
from packages.fetchai.skills.generic_seller.behaviours import (
    GenericServiceRegistrationBehaviour,
)
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

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
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
        """Implement the handler teardown."""
```
The code above contains the logic for handling `FipaMessages` received by the `my_generic_seller` AEA. We use `FipaDialogues` (more on this <a href="../generic-skills-step-by-step/#step-5-create-the-dialogues">below</a>) to keep track of the progress of the negotiation dialogue between the `my_generic_seller` AEA and the `my_generic_buyer` AEA.

In the above `handle` method, we first check if a received message belongs to an existing dialogue or if we have to create a new dialogue (the `recover dialogue` part). Once this is done, we break down the AEA's response to each type of negotiation message, as indicated by the message's performative (the `handle message` part). Therefore, we implement the AEA's response to each negotiation message type in a different handler function.

Below the unused `teardown` function, we continue by adding the following function:

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

The next code block handles `CFP` (call-for-proposal) negotiation messages. Paste the following code below the `_handle_unidentified_dialogue` function:

``` python
    def _handle_cfp(self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue) -> None:
        """
        Handle the CFP.

        If the CFP matches the supplied services then send a PROPOSE, otherwise send a DECLINE.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
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

The above code sends a `PROPOSE` message back to the buyer as a response to its `CFP` if the requested services match our seller agent's supplied services, otherwise it will respond with a `DECLINE` message.

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
        :param fipa_dialogues: the dialogues object
        """
        self.context.logger.info(
            "received DECLINE from sender={}".format(fipa_msg.sender[-5:])
        )
        fipa_dialogues.dialogue_stats.add_dialogue_endstate(
            FipaDialogue.EndState.DECLINED_PROPOSE, fipa_dialogue.is_self_initiated
        )
```
If we receive a decline message from the buyer we close the dialogue and terminate this conversation with `my_generic_buyer`.

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
When `my_generic_buyer` accepts the `Proposal` we send it and sends an `ACCEPT` message, we have to respond with another message (`MATCH_ACCEPT_W_INFORM`) to match the acceptance of the terms of trade and to inform the buyer of the address we would like it to send the funds to. 

Lastly, we must handle an `INFORM` message, which the buyer uses to inform us that it has indeed sent the funds to the provided address. Add the following code at the end of the file:

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
In the above code, we check the `INFORM` message. If it contains a transaction digest, then we verify that the transaction matches the proposal the buyer accepted. If the transaction is valid and we received the funds then we send the data to the buyer. Otherwise, we do not send the data.

The remaining handlers are as follows:
``` python
    def _handle_invalid(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle a fipa message of invalid performative.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
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

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
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
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param ledger_api_msg: the message
        """
        self.context.logger.info(
            "received invalid ledger_api message={}, unidentified dialogue.".format(
                ledger_api_msg
            )
        )

    def _handle_balance(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_msg: the ledger api message
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

        :param ledger_api_msg: the ledger api message
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

        :param ledger_api_msg: the ledger api message
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

        :param ledger_api_msg: the ledger api message
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

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
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
        if oef_search_msg.performative == OefSearchMessage.Performative.SUCCESS:
            self._handle_success(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative == OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param oef_search_msg: the message
        """
        self.context.logger.info(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _handle_success(
        self,
        oef_search_success_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_success_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.info(
            "received oef_search success message={} in dialogue={}.".format(
                oef_search_success_msg, oef_search_dialogue
            )
        )
        target_message = cast(
            OefSearchMessage,
            oef_search_dialogue.get_message_by_id(oef_search_success_msg.target),
        )
        if (
            target_message.performative
            == OefSearchMessage.Performative.REGISTER_SERVICE
        ):
            description = target_message.service_description
            data_model_name = description.data_model.name
            registration_behaviour = cast(
                GenericServiceRegistrationBehaviour,
                self.context.behaviours.service_registration,
            )
            if "location_agent" in data_model_name:
                registration_behaviour.register_service()
            elif "set_service_key" in data_model_name:
                registration_behaviour.register_genus()
            elif (
                "personality_agent" in data_model_name
                and description.values["piece"] == "genus"
            ):
                registration_behaviour.register_classification()
            elif (
                "personality_agent" in data_model_name
                and description.values["piece"] == "classification"
            ):
                self.context.logger.info(
                    "the agent, with its genus and classification, and its service are successfully registered on the SOEF."
                )
            else:
                self.context.logger.warning(
                    f"received soef SUCCESS message as a reply to the following unexpected message: {target_message}"
                )

    def _handle_error(
        self,
        oef_search_error_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_error_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_error_msg, oef_search_dialogue
            )
        )
        target_message = cast(
            OefSearchMessage,
            oef_search_dialogue.get_message_by_id(oef_search_error_msg.target),
        )
        if (
            target_message.performative
            == OefSearchMessage.Performative.REGISTER_SERVICE
        ):
            registration_behaviour = cast(
                GenericServiceRegistrationBehaviour,
                self.context.behaviours.service_registration,
            )
            registration_behaviour.failed_registration_msg = target_message

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
```

The `GenericLedgerApiHandler` deals with `LedgerApiMessages` from the ledger connection and the `GenericOefSearchHandler` handles `OefSearchMessages` from the SOEF connection.

### Step 4: Create the strategy

Next, we are going to create the strategy that we want our `my_generic_seller` AEA to follow. Rename the `my_model.py` file (`my_generic_seller/skills/generic_seller/my_model.py`) to `strategy.py` and replace the stub code with the following:

``` python
import uuid
from typing import Any, Dict, Optional, Tuple

from aea.common import Address
from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import enforce
from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
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
DEFAULT_PERSONALITY_DATA = {"piece": "genus", "value": "data"}
DEFAULT_CLASSIFICATION = {"piece": "classification", "value": "seller"}

DEFAULT_HAS_DATA_SOURCE = False
DEFAULT_DATA_FOR_SALE = {
    "some_generic_data_key": "some_generic_data_value"
}  # type: Optional[Dict[str, Any]]


class GenericStrategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :param kwargs: keyword arguments
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
        self._set_personality_data = kwargs.pop(
            "personality_data", DEFAULT_PERSONALITY_DATA
        )
        enforce(
            len(self._set_personality_data) == 2
            and "piece" in self._set_personality_data
            and "value" in self._set_personality_data,
            "personality_data must contain keys `key` and `value`",
        )
        self._set_classification = kwargs.pop("classification", DEFAULT_CLASSIFICATION)
        enforce(
            len(self._set_classification) == 2
            and "piece" in self._set_classification
            and "value" in self._set_classification,
            "classification must contain keys `key` and `value`",
        )
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

In the above code snippet, we initialise the strategy class by trying to read the variables specific to the strategy from a YAML configuration file. If any variable is not provided, some default values will be used.

The following properties and methods deal with different aspects of the strategy. They should be relatively self-descriptive. Add them under the initialization of the strategy class:

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

    def get_register_personality_description(self) -> Description:
        """
        Get the register personality description.

        :return: a description of the personality
        """
        description = Description(
            self._set_personality_data, data_model=AGENT_PERSONALITY_MODEL,
        )
        return description

    def get_register_classification_description(self) -> Description:
        """
        Get the register classification description.

        :return: a description of the classification
        """
        description = Description(
            self._set_classification, data_model=AGENT_PERSONALITY_MODEL,
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
        :return: bool indicating whether matches or not
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

The helper private function `collect_from_data_source` is where we read data from a sensor or if there are no sensor we use some default data provided (see the `data_for_sale` property).

### Step 5: Create the dialogues

To keep track of the structure and progress of interactions, including negotiations with a buyer AEA and interactions with search nodes and ledgers, we use dialogues. Create a new file in the skill folder (`my_generic_seller/skills/generic_seller/`) and name it `dialogues.py`. Inside this file add the following code:

``` python
from typing import Any, Dict, Optional, Type

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

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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

    __slots__ = ("data_for_sale", "_terms")

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
        :param message_class: the message class
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

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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

    __slots__ = ("_associated_fipa_dialogue",)

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
        :param message_class: the message class
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

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=LedgerApiDialogue,
        )


OefSearchDialogue = BaseOefSearchDialogue


class OefSearchDialogues(Model, BaseOefSearchDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )
```

The `FipaDialogues` class contains negotiation dialogues with each `my_generic_buyer` AEA (and other AEAs) and exposes a number of helpful methods to manage them. This helps us match messages to the dialogues they belong to, access previous messages and enable us to identify possible communications problems between the `my_generic_seller` AEA and the `my_generic_buyer` AEA. It also keeps track of the data that we offer for sale during the proposal phase.

The `FipaDialogues` class extends `BaseFipaDialogues`, which itself derives from the base <a href="../api/protocols/dialogue/base#dialogues-objects">`Dialogues`</a> class. Similarly, the `FipaDialogue` class extends `BaseFipaDialogue` which itself derives from the base <a href="../api/protocols/dialogue/base#dialogue-objects">`Dialogue`</a> class. To learn more about dialogues have a look <a href="../protocol">here</a>.

### Step 6: Update the YAML files

Since we made so many changes to our AEA we have to update the `skill.yaml` (at `my_generic_seller/skills/generic_seller/skill.yaml`). Make sure you update your `skill.yaml` with the following configuration:

``` yaml
name: generic_seller
author: fetchai
version: 0.1.0
type: skill
description: The weather station skill implements the functionality to sell weather
  data.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
fingerprint:
  README.md: QmPb5kHYZyhUN87EKmuahyGqDGgqVdGPyfC1KpGC3xfmcP
  __init__.py: QmTSEedzQySy2nzRCY3F66CBSX52f8s3pWHZTejX4hKC9h
  behaviours.py: QmS9sPCv2yBnhWsmHeaCptpApMtYZipbR39TXixeGK64Ks
  dialogues.py: QmdTW8q1xQ7ajFVsWmuV62ypoT5J2b6Hkyz52LFaWuMEtd
  handlers.py: QmQnQhSaHPUYaJut8bMe2LHEqiZqokMSVfCthVaqrvPbdi
  strategy.py: QmYTUsfv64eRQDevCfMUDQPx2GCtiMLFdacN4sS1E4Fdfx
fingerprint_ignore_patterns: []
connections:
- fetchai/ledger:0.19.0
contracts: []
protocols:
- fetchai/default:1.0.0
- fetchai/fipa:1.0.0
- fetchai/ledger_api:1.0.0
- fetchai/oef_search:1.0.0
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
      data_for_sale:
        generic: data
      has_data_source: false
      is_ledger_tx: true
      location:
        latitude: 51.5194
        longitude: 0.127
      service_data:
        key: seller_service
        value: generic_service
      service_id: generic_service
      unit_price: 10
    class_name: GenericStrategy
is_abstract: false
dependencies: {}
```

We must pay attention to the models and in particular the strategy’s variables. Here we can change the price we would like to sell each data reading for, or the currency we would like to transact with. Lastly, the dependencies are the third party packages we need to install in order to get readings from the sensor.

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
aea install
```

Our newly created AEA is inside the current working directory. Let’s create a new skill for purchasing data. Type the following command:

``` bash
aea scaffold skill generic_buyer
```

This command creates the correct structure for a new skill inside our AEA project. You can locate the newly created skill under the skills folder (`my_generic_buyer/skills/generic_buyer/`) and it must contain the following files:

- `__init__.py`
- `behaviours.py`
- `handlers.py`
- `my_model.py`
- `skills.yaml`

### Step 2: Create the behaviour

Open the `behaviours.py` file (`my_generic_buyer/skills/generic_buyer/behaviours.py`) and replace the stub code with the following:

``` python
from typing import Any, List, Optional, Set, cast

from aea.protocols.dialogue.base import DialogueLabel
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.dialogues import (
    FipaDialogue,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy


DEFAULT_MAX_PROCESSING = 120
DEFAULT_TX_INTERVAL = 2.0
DEFAULT_SEARCH_INTERVAL = 5.0
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class GenericSearchBehaviour(TickerBehaviour):
    """This class implements a search behaviour."""

    def __init__(self, **kwargs: Any):
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
        """Implement the act."""
        strategy = cast(GenericStrategy, self.context.strategy)
        if not strategy.is_searching:
            return
        transaction_behaviour = cast(
            GenericTransactionBehaviour, self.context.behaviours.transaction
        )
        remaining_transactions_count = len(transaction_behaviour.waiting)
        if remaining_transactions_count > 0:
            self.context.logger.info(
                f"Transaction behaviour has {remaining_transactions_count} transactions remaining. Skipping search!"
            )
            return
        strategy.update_search_query_params()
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
        """Implement the task teardown."""


class GenericTransactionBehaviour(TickerBehaviour):
    """A behaviour to sequentially submit transactions to the blockchain."""

    def __init__(self, **kwargs: Any):
        """Initialize the transaction behaviour."""
        tx_interval = cast(
            float, kwargs.pop("transaction_interval", DEFAULT_TX_INTERVAL)
        )
        self.max_processing = cast(
            float, kwargs.pop("max_processing", DEFAULT_MAX_PROCESSING)
        )
        self.processing_time = 0.0
        self.waiting: List[FipaDialogue] = []
        self.processing: Optional[LedgerApiDialogue] = None
        self.timedout: Set[DialogueLabel] = set()
        super().__init__(tick_interval=tx_interval, **kwargs)

    def setup(self) -> None:
        """Setup behaviour."""

    def act(self) -> None:
        """Implement the act."""
        if self.processing is not None:
            if self.processing_time <= self.max_processing:
                # already processing
                self.processing_time += self.tick_interval
                return
            self._timeout_processing()
        if len(self.waiting) == 0:
            # nothing to process
            return
        self._start_processing()

    def _start_processing(self) -> None:
        """Process the next transaction."""
        fipa_dialogue = self.waiting.pop(0)
        self.context.logger.info(
            f"Processing transaction, {len(self.waiting)} transactions remaining"
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
        self.processing_time = 0.0
        self.processing = ledger_api_dialogue
        self.context.logger.info(
            f"requesting transfer transaction from ledger api for message={ledger_api_msg}..."
        )
        self.context.outbox.put_message(message=ledger_api_msg)

    def teardown(self) -> None:
        """Teardown behaviour."""

    def _timeout_processing(self) -> None:
        """Timeout processing."""
        if self.processing is None:
            return
        self.timedout.add(self.processing.dialogue_label)
        self.waiting.append(self.processing.associated_fipa_dialogue)
        self.processing_time = 0.0
        self.processing = None

    def finish_processing(self, ledger_api_dialogue: LedgerApiDialogue) -> None:
        """
        Finish processing.

        :param ledger_api_dialogue: the ledger api dialogue
        """
        if self.processing == ledger_api_dialogue:
            self.processing_time = 0.0
            self.processing = None
            return
        if ledger_api_dialogue.dialogue_label not in self.timedout:
            raise ValueError(
                f"Non-matching dialogues in transaction behaviour: {self.processing} and {ledger_api_dialogue}"
            )
        self.timedout.remove(ledger_api_dialogue.dialogue_label)
        self.context.logger.debug(
            f"Timeout dialogue in transaction processing: {ledger_api_dialogue}"
        )
        # don't reset, as another might be processing

    def failed_processing(self, ledger_api_dialogue: LedgerApiDialogue) -> None:
        """
        Failed processing.

        Currently, we retry processing indefinitely.

        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.finish_processing(ledger_api_dialogue)
        self.waiting.append(ledger_api_dialogue.associated_fipa_dialogue)
```

This <a href="../api/skills/behaviours#tickerbehaviour-objects">`TickerBehaviour`</a> will send a search query to the <a href="../simple-oef">SOEF search node</a> at regular tick intervals.

### Step 3: Create the handler

So far, the AEA is tasked with sending search queries to the <a href="../simple-oef">SOEF search node</a>. However, currently the AEA has no way of handling the responses it receives from the SOEF or messages from other agents.

Let us now implement <a href="../api/skills/base#handler-objects">`Handlers`</a> to deal with the expected incoming messages. Open the `handlers.py` file (`my_generic_buyer/skills/generic_buyer/handlers.py`) and add the following code (replacing the stub code already present in the file):

``` python
import pprint
from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.crypto.ledger_apis import LedgerApis
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
from packages.fetchai.skills.generic_buyer.behaviours import GenericTransactionBehaviour
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
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
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
        """Implement the handler teardown."""
```
You will see that we are following similar logic to the `generic_seller` when we develop the `generic_buyer`’s side of the negotiation. First, we create a new dialogue and store it in the dialogues class. Then we are checking what kind of message we received by checking its performative. So lets start creating our handlers:

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
The above code handles messages referencing unidentified dialogues and responds with an error message to the sender. Next we will handle the `PROPOSE` message received from the `my_generic_seller` AEA:

``` python
    def _handle_propose(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the propose.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
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
When we receive a proposal, we have to check if we have the funds to complete the transaction and if the proposal is acceptable based on our strategy. If the proposal is not affordable or acceptable, we respond with a `DECLINE` message. Otherwise, we send an `ACCEPT` message to the seller.

The next code-block handles the `DECLINE` message that we may receive from the seller as a response to our `CFP` or `ACCEPT` messages:

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
        """
        self.context.logger.info(
            "received DECLINE from sender={}".format(fipa_msg.sender[-5:])
        )
        target_message = fipa_dialogue.get_message_by_id(fipa_msg.target)

        if not target_message:
            raise ValueError("Can not find target message!")  # pragma: nocover

        declined_performative = target_message.performative

        if declined_performative == FipaMessage.Performative.CFP:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_CFP, fipa_dialogue.is_self_initiated
            )
        if declined_performative == FipaMessage.Performative.ACCEPT:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_ACCEPT, fipa_dialogue.is_self_initiated
            )
```
The above code terminates each dialogue with the specific AEA and stores the state of the terminated dialogue (whether it was terminated after a `CFP` or an `ACCEPT`). 

If `my_generic_seller` AEA wants to move on with the sale, it will send a `MATCH_ACCEPT` message. In order to handle this we add the following code:

``` python
    def _handle_match_accept(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the match accept.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
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

            tx_behaviour = cast(
                GenericTransactionBehaviour, self.context.behaviours.transaction
            )
            tx_behaviour.waiting.append(fipa_dialogue)
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
The first thing we are checking is if we enabled our AEA to transact with a ledger. If so, we add this negotiation to the queue of transactions to be processed. If not, we simulate non-ledger payment by sending an inform to the seller that the payment is done (say via bank transfer).

Lastly, we need to handle `INFORM` messages. This is the message that will have our data:

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
        """
        self.context.logger.info(
            "received INFORM from sender={}".format(fipa_msg.sender[-5:])
        )
        if len(fipa_msg.info.keys()) >= 1:
            data = fipa_msg.info
            data_string = pprint.pformat(data)[:1000]
            self.context.logger.info(f"received the following data={data_string}")
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
        """
        self.context.logger.warning(
            "cannot handle fipa message of performative={} in dialogue={}.".format(
                fipa_msg.performative, fipa_dialogue
            )
        )
```

We now need to add handlers for messages received from the `DecisionMaker` and the <a href="../simple-oef">SOEF search node</a>. We need one handler for each type of protocol we use.

To handle the messages in the `oef_search` protocol used by the <a href="../simple-oef">SOEF search node</a> we add the following code in the same file (`my_generic_buyer/skills/generic_buyer/handlers.py`):

``` python
class GenericOefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Call to setup the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
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
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param oef_search_msg: the message
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

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
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
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
```
When we receive a message from the <a href="../simple-oef">SOEF search node</a> of a type `OefSearchMessage.Performative.SEARCH_RESULT`, we are passing the details to the relevant handler method. In the `_handle_search` function we are checking that the response contains some agents and we stop the search if it does. We pick our first agent and we send a `CFP` message.

The last handlers we need are the `GenericSigningHandler` and the `GenericLedgerApiHandler`. These handlers are responsible for `SigningMessages` that we receive from the `DecisionMaker`, and `LedgerApiMessages` that we receive from the ledger connection, respectively.

``` python
class GenericSigningHandler(Handler):
    """Implement the signing handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
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
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, signing_msg: SigningMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param signing_msg: the message
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
        """
        self.context.logger.info("transaction signing was successful.")
        ledger_api_dialogue = signing_dialogue.associated_ledger_api_dialogue
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
        """
        self.context.logger.info(
            "transaction signing was not successful. Error_code={} in dialogue={}".format(
                signing_msg.error_code, signing_dialogue
            )
        )
        signing_msg_ = cast(
            Optional[SigningMessage], signing_dialogue.last_outgoing_message
        )
        if (
            signing_msg_ is not None
            and signing_msg_.performative
            == SigningMessage.Performative.SIGN_TRANSACTION
        ):
            tx_behaviour = cast(
                GenericTransactionBehaviour, self.context.behaviours.transaction
            )
            ledger_api_dialogue = signing_dialogue.associated_ledger_api_dialogue
            tx_behaviour.failed_processing(ledger_api_dialogue)

    def _handle_invalid(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
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

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
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
        elif (
            ledger_api_msg.performative
            == LedgerApiMessage.Performative.TRANSACTION_RECEIPT
        ):
            self._handle_transaction_receipt(ledger_api_msg, ledger_api_dialogue)
        elif ledger_api_msg.performative == LedgerApiMessage.Performative.ERROR:
            self._handle_error(ledger_api_msg, ledger_api_dialogue)
        else:
            self._handle_invalid(ledger_api_msg, ledger_api_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param ledger_api_msg: the message
        """
        self.context.logger.info(
            "received invalid ledger_api message={}, unidentified dialogue.".format(
                ledger_api_msg
            )
        )

    def _handle_balance(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_msg: the ledger api message
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
                f"you have no starting balance on {strategy.ledger_id} ledger! Stopping skill {self.skill_id}."
            )
            self.context.is_active = False

    def _handle_raw_transaction(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of raw_transaction performative.

        :param ledger_api_msg: the ledger api message
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
        signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "proposing the transaction to the decision maker. Waiting for confirmation ..."
        )

    def _handle_transaction_digest(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction_digest performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "transaction was successfully submitted. Transaction digest={}".format(
                ledger_api_msg.transaction_digest
            )
        )
        ledger_api_msg_ = ledger_api_dialogue.reply(
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            target_message=ledger_api_msg,
            transaction_digest=ledger_api_msg.transaction_digest,
        )
        self.context.logger.info("checking transaction is settled.")
        self.context.outbox.put_message(message=ledger_api_msg_)

    def _handle_transaction_receipt(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        fipa_dialogue = ledger_api_dialogue.associated_fipa_dialogue
        is_settled = LedgerApis.is_transaction_settled(
            fipa_dialogue.terms.ledger_id, ledger_api_msg.transaction_receipt.receipt
        )
        tx_behaviour = cast(
            GenericTransactionBehaviour, self.context.behaviours.transaction
        )
        if is_settled:
            tx_behaviour.finish_processing(ledger_api_dialogue)
            ledger_api_msg_ = cast(
                Optional[LedgerApiMessage], ledger_api_dialogue.last_outgoing_message
            )
            if ledger_api_msg_ is None:
                raise ValueError(  # pragma: nocover
                    "Could not retrieve last ledger_api message"
                )
            fipa_msg = cast(Optional[FipaMessage], fipa_dialogue.last_incoming_message)
            if fipa_msg is None:
                raise ValueError("Could not retrieve last fipa message")
            inform_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.INFORM,
                target_message=fipa_msg,
                info={"transaction_digest": ledger_api_msg_.transaction_digest.body},
            )
            self.context.outbox.put_message(message=inform_msg)
            self.context.logger.info(
                "transaction confirmed, informing counterparty={} of transaction digest.".format(
                    fipa_dialogue.dialogue_label.dialogue_opponent_addr[-5:],
                )
            )
        else:
            tx_behaviour.failed_processing(ledger_api_dialogue)
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

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "received ledger_api error message={} in dialogue={}.".format(
                ledger_api_msg, ledger_api_dialogue
            )
        )
        ledger_api_msg_ = cast(
            Optional[LedgerApiMessage], ledger_api_dialogue.last_outgoing_message
        )
        if (
            ledger_api_msg_ is not None
            and ledger_api_msg_.performative
            != LedgerApiMessage.Performative.GET_BALANCE
        ):
            tx_behaviour = cast(
                GenericTransactionBehaviour, self.context.behaviours.transaction
            )
            tx_behaviour.failed_processing(ledger_api_dialogue)

    def _handle_invalid(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of invalid performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "cannot handle ledger_api message of performative={} in dialogue={}.".format(
                ledger_api_msg.performative, ledger_api_dialogue,
            )
        )
```

### Step 4: Create the strategy

We are going to create the strategy that we want our AEA to follow. Rename the `my_model.py` file (in `my_generic_buyer/skills/generic_buyer/`) to `strategy.py` and replace the stub code with the following:

``` python
from typing import Any, Dict, List, Tuple

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
DEFAULT_MIN_QUANTITY = 1
DEFAULT_MAX_QUANTITY = 100

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

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :param kwargs: keyword arguments
        """
        ledger_id = kwargs.pop("ledger_id", None)
        currency_id = kwargs.pop("currency_id", None)
        self._is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)

        self._max_unit_price = kwargs.pop("max_unit_price", DEFAULT_MAX_UNIT_PRICE)
        self._min_quantity = kwargs.pop("min_quantity", DEFAULT_MIN_QUANTITY)
        self._max_quantity = kwargs.pop("max_quantity", DEFAULT_MAX_QUANTITY)
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

Similar to the seller AEA, we initialize the strategy class by trying to read the strategy variables from the YAML file, and if not possible, use some default values. In the following snippet, the two methods after the properties are related to the OEF search service. Add this snippet under the initialization of the strategy class:

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

The following code block checks if the proposal that we received is acceptable according to a strategy:

``` python
    def is_acceptable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an acceptable proposal.

        :param proposal: a description
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
            and proposal.values["price"] > 0
            and proposal.values["quantity"] >= self._min_quantity
            and proposal.values["quantity"] <= self._max_quantity
            and proposal.values["price"]
            <= proposal.values["quantity"] * self._max_unit_price
            and proposal.values["currency_id"] == self._currency_id
            and proposal.values["service_id"] == self._service_id
            and isinstance(proposal.values["tx_nonce"], str)
            and proposal.values["tx_nonce"] != ""
        )
        return result
```

The `is_affordable_proposal` method in the following code block checks if we can afford the transaction based on the funds we have in our wallet on the ledger. The rest of the methods are self-explanatory. 

``` python
    def is_affordable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an affordable proposal.

        :param proposal: a description
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

        :param counterparties: a tuple of counterparties
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
        :param counterparty_address: the counterparty
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
        """

    def update_search_query_params(self) -> None:
        """Update agent location and query for search."""
```

### Step 5: Create the dialogues

As mentioned during the creation of the seller AEA, we should keep track of the various interactions an AEA has with others and this is done via dialogues. Create a new file and name it `dialogues.py` (in `my_generic_buyer/skills/generic_buyer/`). Inside this file add the following code:

``` python
from typing import Any, Optional, Type

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

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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

    __slots__ = (
        "_terms",
        "_associated_ledger_api_dialogue",
    )

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
        :param message_class: the message class
        """
        BaseFipaDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
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

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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

    __slots__ = ("_associated_fipa_dialogue",)

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
        :param message_class: the message class
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

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=LedgerApiDialogue,
        )


OefSearchDialogue = BaseOefSearchDialogue


class OefSearchDialogues(Model, BaseOefSearchDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )


class SigningDialogue(BaseSigningDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("_associated_ledger_api_dialogue",)

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
        :param message_class: the message class
        """
        BaseSigningDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._associated_ledger_api_dialogue = None  # type: Optional[LedgerApiDialogue]

    @property
    def associated_ledger_api_dialogue(self) -> LedgerApiDialogue:
        """Get associated_ledger_api_dialogue."""
        if self._associated_ledger_api_dialogue is None:
            raise AEAEnforceError("LedgerApiDialogue not set!")
        return self._associated_ledger_api_dialogue

    @associated_ledger_api_dialogue.setter
    def associated_ledger_api_dialogue(
        self, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """Set associated_ledger_api_dialogue"""
        enforce(
            self._associated_ledger_api_dialogue is None,
            "LedgerApiDialogue already set!",
        )
        self._associated_ledger_api_dialogue = ledger_api_dialogue


class SigningDialogues(Model, BaseSigningDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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

The various dialogues classes in the above code snippet store dialogues with other AEAs, services and components, (e.g. SOEF search node via the `fetchai/soef` connection, ledgers via the `fetchai/ledger` connection and the decision maker). They expose useful methods to manipulate these interactions, access previous messages, and enable us to identify possible communications problems between `my_generic_seller` and `my_generic_buyer` AEAs.

### Step 6: Update the YAML files

After making so many changes to our skill, we have to update the `skill.yaml` configuration file so it reflects our newly created classes, and contains the values used by the strategy. Make sure `skill.yaml` contains the following configuration:

``` yaml
name: generic_buyer
author: fetchai
version: 0.1.0
type: skill
description: The weather client skill implements the skill to purchase weather data.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
fingerprint:
  README.md: QmTR91jm7WfJpmabisy74NR5mc35YXjDU1zQAUKZeHRw8L
  __init__.py: QmU5vrC8FipyjfS5biNa6qDWdp4aeH5h4YTtbFDmCg8Chj
  behaviours.py: QmNwvSjEz4kzM3gWtnKbZVFJc2Z85Nb748CWAK4C4Sa4nT
  dialogues.py: QmNen91qQDWy4bNBKrB3LabAP5iRf29B8iwYss4NB13iNU
  handlers.py: QmZfudXXbdiREiViuwPZDXoQQyXT2ySQHdF7psQsohZXQy
  strategy.py: QmcrwaEWvKHDCNti8QjRhB4utJBJn5L8GpD27Uy9zHwKhY
fingerprint_ignore_patterns: []
connections:
- fetchai/ledger:0.19.0
contracts: []
protocols:
- fetchai/default:1.0.0
- fetchai/fipa:1.0.0
- fetchai/ledger_api:1.0.0
- fetchai/oef_search:1.0.0
- fetchai/signing:1.0.0
skills: []
behaviours:
  search:
    args:
      search_interval: 5
    class_name: GenericSearchBehaviour
  transaction:
    args:
      max_processing: 420
      transaction_interval: 2
    class_name: GenericTransactionBehaviour
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
      is_ledger_tx: true
      location:
        latitude: 51.5194
        longitude: 0.127
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      min_quantity: 1
      search_query:
        constraint_type: ==
        search_key: seller_service
        search_value: generic_service
      search_radius: 5.0
      service_id: generic_service
      stop_searching_on_result: true
    class_name: GenericStrategy
is_abstract: false
dependencies: {}
```
We must pay attention to the models and the strategy’s variables. Here we can change the price we would like to buy each reading at, the maximum transaction fee we are prepared to pay, and so on. 

Finally, we fingerprint our new skill:

``` bash
aea fingerprint skill fetchai/generic_buyer:0.1.0
```

This will hash each file and save the hash in the fingerprint. This way, in the future we can easily track if any of the files have changed.

## Run the AEAs

### Create private keys

For each AEA, create a private key:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Next, create a private key to secure the AEA's communications:
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

Finally, certify the key for use by the connections that request that:
``` bash
aea issue-certificates
```

### Update the AEA configurations

In both AEAs run:
``` bash
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
```

### Fund the buyer AEA

Create some wealth for your buyer on the Fetch.ai testnet (this operation might take a while).

``` bash
aea generate-wealth fetchai --sync
```

### Run seller AEA

Add the remaining packages for the seller AEA, then run it:

``` bash
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add protocol fetchai/fipa:1.0.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea run
```

Once you see a message of the form `To join its network use multiaddr: ['SOME_ADDRESS']` take note of the address.

#### Run buyer AEA

Add the remaining packages for the buyer AEA:

``` bash
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add protocol fetchai/fipa:1.0.0
aea add protocol fetchai/signing:1.0.0
aea install
aea build
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
```

Then, update the configuration of the buyer AEA's P2P connection:

``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}'
```

where `SOME_ADDRESS` is replaced accordingly.

Then run the buyer AEA:
``` bash
aea run
```

You will see that the AEAs negotiate and then transact using the StargateWorld testnet.

## Delete the AEAs

When you are done, go up a level and delete the AEAs.
``` bash
cd ..
aea delete my_generic_seller
aea delete my_generic_buyer
```

## Next steps

You have completed the "Getting Started" series. Congratulations!

The following guide provides some hints on <a href="../development-setup">AEA development setup</a>.

### Recommended

We recommend you build your own AEA next. There are many helpful guides and demos in the documentation, and a developer community on <a href="https://discord.com/invite/btedfjPJTj" target="_blank">Discord</a>. Speak to you there!

<br />
