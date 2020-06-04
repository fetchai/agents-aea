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

"""This package contains the handlers of a thermometer AEA."""

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
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=DefaultMessage.protocol_id,
            message=default_msg,
        )

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
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FipaMessage.protocol_id,
                message=proposal_msg,
            )
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
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FipaMessage.protocol_id,
                message=decline_msg,
            )

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
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=FipaMessage.protocol_id,
            message=match_accept_msg,
        )

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
                self.context.outbox.put_message(
                    to=msg.counterparty,
                    sender=self.context.agent_address,
                    protocol_id=FipaMessage.protocol_id,
                    message=inform_msg,
                )
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
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FipaMessage.protocol_id,
                message=inform_msg,
            )
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
