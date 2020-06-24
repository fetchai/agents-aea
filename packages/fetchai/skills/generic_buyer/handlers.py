# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This package contains handlers for the generic buyer skill."""

import pprint
from typing import Dict, Optional, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.transaction.base import Transfer
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.dialogues import (
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
)
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy


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

    def _handle_propose(self, msg: FipaMessage, fipa_dialogue: FipaDialogue) -> None:
        """
        Handle the propose.

        :param msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received proposal={} from sender={}".format(
                self.context.agent_name, msg.proposal.values, msg.counterparty[-5:]
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        acceptable = strategy.is_acceptable_proposal(msg.proposal)
        affordable = strategy.is_affordable_proposal(msg.proposal)
        if acceptable and affordable:
            strategy.is_searching = False
            self.context.logger.info(
                "[{}]: accepting the proposal from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
            fipa_dialogue.proposal = msg.proposal
            accept_msg = FipaMessage(
                message_id=msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=msg.message_id,
                performative=FipaMessage.Performative.ACCEPT,
            )
            accept_msg.counterparty = msg.counterparty
            fipa_dialogue.update(accept_msg)
            self.context.outbox.put_message(message=accept_msg)
        else:
            self.context.logger.info(
                "[{}]: declining the proposal from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
            decline_msg = FipaMessage(
                message_id=msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=msg.message_id,
                performative=FipaMessage.Performative.DECLINE,
            )
            decline_msg.counterparty = msg.counterparty
            fipa_dialogue.update(decline_msg)
            self.context.outbox.put_message(message=decline_msg)

    def _handle_decline(self, msg: FipaMessage, fipa_dialogue: FipaDialogue) -> None:
        """
        Handle the decline.

        :param msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received DECLINE from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        target = msg.get("target")
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        if target == 1:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_CFP, fipa_dialogue.is_self_initiated
            )
        elif target == 3:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_ACCEPT, fipa_dialogue.is_self_initiated
            )

    def _handle_match_accept(
        self, msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the match accept.

        :param msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "[{}]: received MATCH_ACCEPT_W_INFORM from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_ledger_tx:
            transfer_address = msg.info.get("address", None)
            if transfer_address is None or not isinstance(transfer_address, str):
                transfer_address = msg.counterparty
            transfer = Transfer(
                sender_addr=self.context.address,
                counterparty_addr=transfer_address,
                amount_by_currency_id={
                    fipa_dialogue.proposal.values[
                        "currency_id"
                    ]: -fipa_dialogue.proposal.values["price"]
                },
                nonce=fipa_dialogue.proposal.values["tx_nonce"],
                service_reference="weather_data_purchase",
            )
            ledger_api_dialogues = cast(
                LedgerApiDialogues, self.context.ledger_api_dialogues
            )
            ledger_api_msg = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_TRANSFER_TRANSACTION,
                dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
                transfer=transfer,
                ledger_id=fipa_dialogue.proposal.values["ledger_id"],
            )
            ledger_api_dialogue = ledger_api_dialogues.update(ledger_api_msg)
            assert (
                ledger_api_dialogue is not None
            ), "Error when creating ledger api dialogue."
            # associate ledger api dialogue with fipa dialogue
            ledger_api_dialogue = cast(LedgerApiDialogue, ledger_api_dialogue)
            ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
            fipa_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
            # send message
            self.context.decision_maker_message_queue.put_nowait(ledger_api_msg)
            self.context.logger.info(
                "[{}]: getting transfer transaction from ledger api...".format(
                    self.context.agent_name
                )
            )
        else:
            new_message_id = msg.message_id + 1
            new_target = msg.message_id
            inform_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FipaMessage.Performative.INFORM,
                info={"Done": "Sending payment via bank transfer"},
            )
            inform_msg.counterparty = msg.counterparty
            fipa_dialogue.update(inform_msg)
            self.context.outbox.put_message(message=inform_msg)
            self.context.logger.info(
                "[{}]: informing counterparty={} of payment.".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )

    def _handle_inform(self, msg: FipaMessage, dialogue: FipaDialogue) -> None:
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
        if len(msg.info.keys()) >= 1:
            data = msg.info
            self.context.logger.info(
                "[{}]: received the following data={}".format(
                    self.context.agent_name, pprint.pformat(data)
                )
            )
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
            )
        else:
            self.context.logger.info(
                "[{}]: received no data from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
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
            strategy = cast(GenericStrategy, self.context.strategy)
            # stopping search
            strategy.is_searching = False
            # pick first agent found
            opponent_addr = agents[0]
            query = strategy.get_service_query()
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            cfp_msg = FipaMessage(
                message_id=FipaDialogue.STARTING_MESSAGE_ID,
                dialogue_reference=fipa_dialogues.new_self_initiated_dialogue_reference(),
                performative=FipaMessage.Performative.CFP,
                target=FipaDialogue.STARTING_TARGET,
                query=query,
            )
            cfp_msg.counterparty = opponent_addr
            fipa_dialogues.update(cfp_msg)
            self.context.outbox.put_message(message=cfp_msg)
            self.context.logger.info(
                "[{}]: sending CFP to agent={}".format(
                    self.context.agent_name, opponent_addr[-5:]
                )
            )
        else:
            self.context.logger.info(
                "[{}]: found no agents, continue searching.".format(
                    self.context.agent_name
                )
            )


class GenericTransactionHandler(Handler):
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
            tx_msg_response.performative
            == TransactionMessage.Performative.SIGNED_TRANSACTION
        ):
            self.context.logger.info(
                "[{}]: transaction signing was successful.".format(
                    self.context.agent_name
                )
            )
            self._send_transaction_to_ledger(tx_msg_response)
            self.context.logger.info(
                "[{}]: sending transaction to ledger.".format(self.context.agent_name)
            )
        else:
            self.context.logger.info(
                "[{}]: transaction signing was not successful. Error_code={}".format(
                    self.context.agent_name, tx_msg_response.error_code
                )
            )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _send_transaction_to_ledger(self, tx_msg: TransactionMessage) -> None:
        """
        Send the transaction message to the ledger.

        :param tx_msg: the transaction message received.
        :return: None
        """
        # find relevant fipa dialogue
        dialogue_label = DialogueLabel.from_json(
            cast(Dict[str, str], tx_msg.skill_callback_info.get("dialogue_label"))
        )
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        fipa_dialogue = fipa_dialogues.get_dialogue_from_label(dialogue_label)
        assert fipa_dialogue is not None, "Error when retrieving fipa dialogue."
        fipa_dialogue = cast(FipaDialogue, fipa_dialogue)
        assert (
            fipa_dialogue.associated_ledger_api_dialogue is not None
        ), "Error when retrieving ledger_api dialogue."
        # create ledger api message and dialogue
        last_ledger_api_msg = (
            fipa_dialogue.associated_ledger_api_dialogue.last_incoming_message
        )
        assert (
            last_ledger_api_msg is not None
        ), "Could not retrieve last message in ledger api dialogue"
        ledger_api_msg = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            dialogue_reference=last_ledger_api_msg.dialogue_reference,
            target=last_ledger_api_msg.message_id,
            message_id=last_ledger_api_msg.message_id + 1,
            ledger_id=tx_msg.crypto_id,
            signed_tx=tx_msg.signed_transaction,
        )
        ledger_api_msg.counterparty = tx_msg.crypto_id
        fipa_dialogue.associated_ledger_api_dialogue.update(ledger_api_msg)
        # associate ledger api dialogue with fipa dialogue and send message
        self.context.outbox.put_message(message=ledger_api_msg)


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
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_dialogue = cast(
            LedgerApiDialogue, ledger_api_dialogues.update(ledger_api_msg)
        )
        if (
            ledger_api_dialogue is None
            or ledger_api_dialogue.associated_fipa_dialogue is None
        ):
            self.context.logger.info(
                "[{}]: cannot recover associate fipa dialogue.".format(
                    self.context.agent_name
                )
            )
            return
        fipa_dialogue = ledger_api_dialogue.associated_fipa_dialogue
        if ledger_api_msg.performative == LedgerApiMessage.Performative.TRANSACTION:
            tx_msg = TransactionMessage(
                performative=TransactionMessage.Performative.SIGN_TRANSACTION,
                skill_callback_ids=(self.context.skill_id,),
                crypto_id=ledger_api_msg.ledger_id,
                transaction=ledger_api_msg.transaction,
                skill_callback_info={
                    "dialogue_label": fipa_dialogue.dialogue_label.json
                },
            )
            self.context.decision_maker_message_queue.put_nowait(tx_msg)
            self.context.logger.info(
                "[{}]: proposing the transaction to the decision maker. Waiting for confirmation ...".format(
                    self.context.agent_name
                )
            )
        elif (
            ledger_api_msg.performative
            == LedgerApiMessage.Performative.TRANSACTION_DIGEST
        ):
            self.context.logger.info(
                "[{}]: transaction was successful. Transaction digest={}".format(
                    self.context.agent_name, ledger_api_msg.transaction_digest
                )
            )
            fipa_msg = cast(FipaMessage, fipa_dialogue.last_incoming_message)
            inform_msg = FipaMessage(
                message_id=fipa_msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=fipa_msg.message_id,
                performative=FipaMessage.Performative.INFORM,
                info={"transaction_digest": ledger_api_msg.transaction_digest},
            )
            inform_msg.counterparty = (
                fipa_dialogue.dialogue_label.dialogue_opponent_addr
            )
            fipa_dialogue.update(inform_msg)
            self.context.outbox.put_message(message=inform_msg)
            self.context.logger.info(
                "[{}]: informing counterparty={} of transaction digest.".format(
                    self.context.agent_name,
                    fipa_dialogue.dialogue_label.dialogue_opponent_addr[-5:],
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
