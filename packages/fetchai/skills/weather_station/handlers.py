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

import logging
from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.helpers.search.models import Description, Query
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer
from packages.fetchai.skills.weather_station.dialogues import Dialogue, Dialogues
from packages.fetchai.skills.weather_station.strategy import Strategy

logger = logging.getLogger("aea.weather_station_skill")


class FIPAHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]

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
        fipa_msg = cast(FIPAMessage, message)
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
                    message.counterparty,
                    dialogue_reference=dialogue_reference,
                    is_seller=True,
                ),
            )
            dialogue.incoming_extend(fipa_msg)
        else:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FIPAMessage.Performative.CFP:
            self._handle_cfp(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.ACCEPT:
            self._handle_accept(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, msg: FIPAMessage) -> None:
        """
        Handle an unidentified dialogue.

        Respond to the sender with a default message containing the appropriate error information.

        :param msg: the message

        :return: None
        """
        logger.info("[{}]: unidentified dialogue.".format(self.context.agent_name))
        default_msg = DefaultMessage(
            type=DefaultMessage.Type.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE.value,
            error_msg="Invalid dialogue.",
            error_data="fipa_message",
        )  # TODO: send FIPASerializer().encode(msg)
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(default_msg),
        )

    def _handle_cfp(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle the CFP.

        If the CFP matches the supplied services then send a PROPOSE, otherwise send a DECLINE.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = msg.message_id + 1
        new_target = msg.message_id
        logger.info(
            "[{}]: received CFP from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        query = cast(Query, msg.query)
        strategy = cast(Strategy, self.context.strategy)

        if strategy.is_matching_supply(query):
            proposal, weather_data = strategy.generate_proposal_and_data(
                query, msg.counterparty
            )
            dialogue.weather_data = weather_data
            dialogue.proposal = proposal
            logger.info(
                "[{}]: sending sender={} a PROPOSE with proposal={}".format(
                    self.context.agent_name, msg.counterparty[-5:], proposal.values
                )
            )
            proposal_msg = FIPAMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FIPAMessage.Performative.PROPOSE,
                proposal=[proposal],
            )
            dialogue.outgoing_extend(proposal_msg)
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(proposal_msg),
            )
        else:
            logger.info(
                "[{}]: declined the CFP from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
            decline_msg = FIPAMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FIPAMessage.Performative.DECLINE,
            )
            dialogue.outgoing_extend(decline_msg)
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(decline_msg),
            )

    def _handle_decline(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle the DECLINE.

        Close the dialogue.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        logger.info(
            "[{}]: received DECLINE from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        dialogues = cast(Dialogues, self.context.dialogues)
        dialogues.dialogue_stats.add_dialogue_endstate(
            Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated
        )

    def _handle_accept(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle the ACCEPT.

        Respond with a MATCH_ACCEPT_W_INFORM which contains the address to send the funds to.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = msg.message_id + 1
        new_target = msg.message_id
        logger.info(
            "[{}]: received ACCEPT from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        logger.info(
            "[{}]: sending MATCH_ACCEPT_W_INFORM to sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        proposal = cast(Description, dialogue.proposal)
        identifier = cast(str, proposal.values.get("ledger_id"))
        match_accept_msg = FIPAMessage(
            message_id=new_message_id,
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            target=new_target,
            performative=FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={"address": self.context.agent_addresses[identifier], },
        )
        dialogue.outgoing_extend(match_accept_msg)
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=FIPAMessage.protocol_id,
            message=FIPASerializer().encode(match_accept_msg),
        )

    def _handle_inform(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
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
        logger.info(
            "[{}]: received INFORM from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )

        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_ledger_tx and ("transaction_digest" in msg.info.keys()):
            tx_digest = msg.info["transaction_digest"]
            logger.info(
                "[{}]: checking whether transaction={} has been received ...".format(
                    self.context.agent_name, tx_digest
                )
            )
            proposal = cast(Description, dialogue.proposal)
            ledger_id = cast(str, proposal.values.get("ledger_id"))
            is_valid = self.context.ledger_apis.is_tx_valid(
                ledger_id,
                tx_digest,
                self.context.agent_addresses[ledger_id],
                msg.counterparty,
                cast(str, proposal.values.get("tx_nonce")),
                cast(int, proposal.values.get("price")),
            )
            # TODO: check the tx_digest references a transaction with the correct terms
            if is_valid:
                token_balance = self.context.ledger_apis.token_balance(
                    ledger_id, cast(str, self.context.agent_addresses.get(ledger_id))
                )
                logger.info(
                    "[{}]: transaction={} settled, new balance={}. Sending data to sender={}".format(
                        self.context.agent_name,
                        tx_digest,
                        token_balance,
                        msg.counterparty[-5:],
                    )
                )
                inform_msg = FIPAMessage(
                    message_id=new_message_id,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=new_target,
                    performative=FIPAMessage.Performative.INFORM,
                    info=dialogue.weather_data,
                )
                dialogue.outgoing_extend(inform_msg)
                self.context.outbox.put_message(
                    to=msg.counterparty,
                    sender=self.context.agent_address,
                    protocol_id=FIPAMessage.protocol_id,
                    message=FIPASerializer().encode(inform_msg),
                )
                dialogues = cast(Dialogues, self.context.dialogues)
                dialogues.dialogue_stats.add_dialogue_endstate(
                    Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
                )
            else:
                logger.info(
                    "[{}]: transaction={} not settled, aborting".format(
                        self.context.agent_name, tx_digest
                    )
                )
        elif "Done" in msg.info.keys():
            inform_msg = FIPAMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FIPAMessage.Performative.INFORM,
                info=dialogue.weather_data,
            )
            dialogue.outgoing_extend(inform_msg)
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(inform_msg),
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
            )
        else:
            logger.warning(
                "[{}]: did not receive transaction digest from sender={}.".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
