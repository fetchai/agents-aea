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

"""This package contains the handlers of a generic seller AEA."""

import time
from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.helpers.search.models import Description, Query
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_seller.dialogues import (
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.generic_seller.strategy import GenericStrategy


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
            self._handle_decline(fipa_msg, fipa_dialogue)
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

    def _handle_cfp(self, msg: FipaMessage, dialogue: FipaDialogue) -> None:
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
        strategy = cast(GenericStrategy, self.context.strategy)

        if strategy.is_matching_supply(query):
            proposal, data_for_sale = strategy.generate_proposal_and_data(
                query, msg.counterparty
            )
            dialogue.data_for_sale = data_for_sale
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

    def _handle_decline(self, msg: FipaMessage, dialogue: FipaDialogue) -> None:
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
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        fipa_dialogues.dialogue_stats.add_dialogue_endstate(
            FipaDialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated
        )

    def _handle_accept(self, msg: FipaMessage, dialogue: FipaDialogue) -> None:
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

    def _handle_inform(self, msg: FipaMessage, dialogue: FipaDialogue) -> None:
        """
        Handle the INFORM.

        If the INFORM message contains the transaction_digest then verify that it is settled, otherwise do nothing.
        If the transaction is settled, send the data, otherwise do nothing.

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

        strategy = cast(GenericStrategy, self.context.strategy)
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
                is_valid = self.context.ledger_apis.is_transaction_valid(
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
                balance = self.context.ledger_apis.get_balance(
                    ledger_id, cast(str, self.context.agent_addresses.get(ledger_id))
                )
                self.context.logger.info(
                    "[{}]: transaction={} settled, new balance={}. Sending data to sender={}".format(
                        self.context.agent_name,
                        tx_digest,
                        balance,
                        msg.counterparty[-5:],
                    )
                )
                inform_msg = FipaMessage(
                    message_id=new_message_id,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=new_target,
                    performative=FipaMessage.Performative.INFORM,
                    info=dialogue.data_for_sale,
                )
                inform_msg.counterparty = msg.counterparty
                dialogue.update(inform_msg)
                self.context.outbox.put_message(message=inform_msg)
                fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
                fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                    FipaDialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
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
                info=dialogue.data_for_sale,
            )
            inform_msg.counterparty = msg.counterparty
            dialogue.update(inform_msg)
            self.context.outbox.put_message(message=inform_msg)
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
            )
        else:
            self.context.logger.warning(
                "[{}]: did not receive transaction digest from sender={}.".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )

    def _handle_invalid(self, msg: FipaMessage, dialogue: FipaDialogue) -> None:
        """
        Handle a fipa message of invalid performative.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle fipa message of performative={}.".format(
                self.context.agent_name, msg.performative
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
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_dialogue = cast(
            Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
        )
        if ledger_api_dialogue is None:
            self.context.logger.info(
                "[{}]: received invalid ledger_api message={}.".format(
                    self.context.agent_name, ledger_api_msg
                )
            )
            return

        strategy = cast(GenericStrategy, self.context.strategy)
        if ledger_api_msg.performative == LedgerApiMessage.Performative.BALANCE:
            self.context.logger.info(
                "[{}]: starting balance on {} ledger={}.".format(
                    self.context.agent_name, strategy.ledger_id, ledger_api_msg.balance,
                )
            )
        elif ledger_api_msg.performative == LedgerApiMessage.Performative.ERROR:
            self.context.logger.info(
                "[{}]: received ledger_api error message={}.".format(
                    self.context.agent_name, ledger_api_msg
                )
            )
        else:
            self.context.logger.warning(
                "[{}]: cannot handle ledger_api message of performative={}.".format(
                    self.context.agent_name, ledger_api_msg.performative
                )
            )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


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
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_dialogue = cast(
            Optional[OefSearchDialogue], oef_search_dialogues.update(oef_search_msg)
        )
        if oef_search_dialogue is None:
            self.context.logger.info(
                "[{}]: received invalid oef_search message={}.".format(
                    self.context.agent_name, oef_search_msg
                )
            )
            return

        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self.context.logger.info(
                "[{}]: received oef_search error message={}.".format(
                    self.context.agent_name, oef_search_msg
                )
            )
        else:
            self.context.logger.warning(
                "[{}]: cannot handle oef_search message of performative={}.".format(
                    self.context.agent_name, oef_search_msg.performative
                )
            )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
