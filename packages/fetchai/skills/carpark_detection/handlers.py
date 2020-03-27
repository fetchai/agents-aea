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

"""This package contains a scaffold of a handler."""

from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.helpers.search.models import Description, Query
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.fipa.serialization import FipaSerializer
from packages.fetchai.skills.carpark_detection.dialogues import Dialogue, Dialogues
from packages.fetchai.skills.carpark_detection.strategy import Strategy


class FIPAHandler(Handler):
    """This class scaffolds a handler."""

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
        # convenience representations
        fipa_msg = cast(FipaMessage, message)
        dialogue_reference = fipa_msg.dialogue_reference

        # recover dialogue
        dialogues = cast(Dialogues, self.context.dialogues)
        if dialogues.is_belonging_to_registered_dialogue(
            fipa_msg, self.context.agent_address
        ):
            dialogue = cast(
                Dialogue, dialogues.get_dialogue(fipa_msg, self.context.agent_address)
            )
            dialogue.incoming_extend(fipa_msg)
        elif dialogues.is_permitted_for_new_dialogue(fipa_msg):
            dialogue = cast(
                Dialogue,
                dialogues.create_opponent_initiated(
                    fipa_msg.counterparty, dialogue_reference, is_seller=True
                ),
            )
            dialogue.incoming_extend(fipa_msg)
        else:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FipaMessage.Performative.CFP:
            self._handle_cfp(fipa_msg, dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.ACCEPT:
            self._handle_accept(fipa_msg, dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, dialogue)

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
            error_data="fipa_message",
        )  # FipaSerializer().encode(msg)
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(default_msg),
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

        if strategy.is_matching_supply(query) and strategy.has_data():
            proposal, carpark_data = strategy.generate_proposal_and_data(
                query, msg.counterparty
            )
            dialogue.carpark_data = carpark_data
            dialogue.proposal = proposal
            self.context.logger.info(
                "[{}]: sending sender={} a PROPOSE with proposal={}".format(
                    self.context.agent_name, msg.counterparty[-5:], proposal.values
                )
            )
            proposal_msg = FipaMessage(
                message_id=new_message_id,
                target=new_target,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                performative=FipaMessage.Performative.PROPOSE,
                proposal=proposal,
            )
            dialogue.outgoing_extend(proposal_msg)
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FipaMessage.protocol_id,
                message=FipaSerializer().encode(proposal_msg),
            )

            strategy.db.set_dialogue_status(
                str(dialogue.dialogue_label),
                msg.counterparty[-5:],
                "received_cfp",
                "send_proposal",
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
            dialogue.outgoing_extend(decline_msg)
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FipaMessage.protocol_id,
                message=FipaSerializer().encode(decline_msg),
            )

            strategy.db.set_dialogue_status(
                str(dialogue.dialogue_label),
                msg.counterparty[-5:],
                "received_cfp",
                "send_no_proposal",
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
        strategy = cast(Strategy, self.context.strategy)
        strategy.db.set_dialogue_status(
            str(dialogue.dialogue_label),
            msg.counterparty[-5:],
            "received_decline",
            "[NONE]",
        )
        # dialogues = cast(Dialogues, self.context.dialogues)
        # dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_PROPOSE)

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
        dialogue.outgoing_extend(match_accept_msg)
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=FipaMessage.protocol_id,
            message=FipaSerializer().encode(match_accept_msg),
        )
        strategy = cast(Strategy, self.context.strategy)
        strategy.db.set_dialogue_status(
            str(dialogue.dialogue_label),
            msg.counterparty[-5:],
            "received_accept",
            "send_match_accept",
        )

    def _handle_inform(self, msg: FipaMessage, dialogue: Dialogue) -> None:
        """
        Handle the INFORM.

        If the INFORM message contains the transaction_digest then verify that it is settled, otherwise do nothing.
        If the transaction is settled send the weather data, otherwise do nothing.

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

        json_data = msg.info
        if "transaction_digest" in json_data.keys():
            tx_digest = json_data["transaction_digest"]
            self.context.logger.info(
                "[{}]: checking whether transaction={} has been received ...".format(
                    self.context.agent_name, tx_digest
                )
            )
            proposal = cast(Description, dialogue.proposal)
            ledger_id = cast(str, proposal.values.get("ledger_id"))
            total_price = cast(int, proposal.values.get("price"))
            is_valid = self.context.ledger_apis.is_tx_valid(
                ledger_id,
                tx_digest,
                self.context.agent_addresses[ledger_id],
                msg.counterparty,
                cast(str, proposal.values.get("tx_nonce")),
                cast(int, proposal.values.get("price")),
            )
            if is_valid:
                token_balance = self.context.ledger_apis.token_balance(
                    ledger_id, cast(str, self.context.agent_addresses.get(ledger_id))
                )

                strategy = cast(Strategy, self.context.strategy)
                strategy.record_balance(token_balance)

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
                    info=dialogue.carpark_data,
                )
                dialogue.outgoing_extend(inform_msg)
                self.context.outbox.put_message(
                    to=msg.counterparty,
                    sender=self.context.agent_address,
                    protocol_id=FipaMessage.protocol_id,
                    message=FipaSerializer().encode(inform_msg),
                )
                # dialogues = cast(Dialogues, self.context.dialogues)
                # dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.SUCCESSFUL)
                strategy.db.add_in_progress_transaction(
                    tx_digest,
                    msg.counterparty[-5:],
                    self.context.agent_name,
                    total_price,
                )
                strategy.db.set_transaction_complete(tx_digest)
                strategy.db.set_dialogue_status(
                    str(dialogue.dialogue_label),
                    msg.counterparty[-5:],
                    "transaction_complete",
                    "send_request_data",
                )
            else:
                self.context.logger.info(
                    "[{}]: transaction={} not settled, aborting".format(
                        self.context.agent_name, tx_digest
                    )
                )
        else:
            self.context.logger.info(
                "[{}]: did not receive transaction digest from sender={}.".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
