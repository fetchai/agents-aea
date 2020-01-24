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
import pprint
from typing import Any, Dict, List, Optional, cast

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Description
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer
from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.skills.weather_client.dialogues import Dialogue, Dialogues
from packages.fetchai.skills.weather_client.strategy import Strategy

logger = logging.getLogger("aea.weather_client_skill")


class FIPAHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]

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
        # convenience representations
        fipa_msg = cast(FIPAMessage, message)

        # recover dialogue
        dialogues = cast(Dialogues, self.context.dialogues)
        if dialogues.is_belonging_to_registered_dialogue(
            fipa_msg, self.context.agent_address
        ):
            dialogue = cast(
                Dialogue, dialogues.get_dialogue(fipa_msg, self.context.agent_address)
            )
            dialogue.incoming_extend(fipa_msg)
        else:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FIPAMessage.Performative.PROPOSE:
            self._handle_propose(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM:
            self._handle_match_accept(fipa_msg, dialogue)
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

        :param msg: the message
        """
        logger.info("[{}]: unidentified dialogue.".format(self.context.agent_name))
        default_msg = DefaultMessage(
            type=DefaultMessage.Type.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE.value,
            error_msg="Invalid dialogue.",
            error_data="fipa_message",
        )  # TODO: send back FIPASerializer().encode(msg))
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(default_msg),
        )

    def _handle_propose(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle the propose.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = msg.message_id + 1
        new_target_id = msg.message_id
        proposals = msg.proposal

        if proposals is not []:
            # only take the first proposal
            proposal = proposals[0]
            logger.info(
                "[{}]: received proposal={} from sender={}".format(
                    self.context.agent_name, proposal.values, msg.counterparty[-5:]
                )
            )
            strategy = cast(Strategy, self.context.strategy)
            acceptable = strategy.is_acceptable_proposal(proposal)
            affordable = strategy.is_affordable_proposal(proposal)
            if acceptable and affordable:
                strategy.is_searching = False
                logger.info(
                    "[{}]: accepting the proposal from sender={}".format(
                        self.context.agent_name, msg.counterparty[-5:]
                    )
                )
                dialogue.proposal = proposal
                accept_msg = FIPAMessage(
                    message_id=new_message_id,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=new_target_id,
                    performative=FIPAMessage.Performative.ACCEPT,
                )
                dialogue.outgoing_extend(accept_msg)
                self.context.outbox.put_message(
                    to=msg.counterparty,
                    sender=self.context.agent_address,
                    protocol_id=FIPAMessage.protocol_id,
                    message=FIPASerializer().encode(accept_msg),
                )
            else:
                logger.info(
                    "[{}]: declining the proposal from sender={}".format(
                        self.context.agent_name, msg.counterparty[-5:]
                    )
                )
                decline_msg = FIPAMessage(
                    message_id=new_message_id,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=new_target_id,
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
        Handle the decline.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        logger.info(
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

    def _handle_match_accept(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle the match accept.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_ledger_tx:
            logger.info(
                "[{}]: received MATCH_ACCEPT_W_INFORM from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
            info = msg.info
            address = cast(str, info.get("address"))
            proposal = cast(Description, dialogue.proposal)
            tx_msg = TransactionMessage(
                performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
                skill_callback_ids=["weather_client"],
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
                info={
                    "dialogue_label": dialogue.dialogue_label.json,
                },
                tx_nonce=proposal.values.get("tx_nonce")
            )
            self.context.decision_maker_message_queue.put_nowait(tx_msg)
            logger.info(
                "[{}]: proposing the transaction to the decision maker. Waiting for confirmation ...".format(
                    self.context.agent_name
                )
            )
        else:
            new_message_id = msg.message_id + 1
            new_target = msg.message_id
            inform_msg = FIPAMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FIPAMessage.Performative.INFORM,
                info={"Done": "Sending payment via bank transfer"},
            )
            dialogue.outgoing_extend(inform_msg)
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(inform_msg),
            )
            logger.info(
                "[{}]: informing counterparty={} of payment.".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )

    def _handle_inform(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle the match inform.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        logger.info(
            "[{}]: received INFORM from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        if "weather_data" in msg.info.keys():
            weather_data = msg.info["weather_data"]
            logger.info(
                "[{}]: received the following weather data={}".format(
                    self.context.agent_name, pprint.pformat(weather_data)
                )
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
            )
        else:
            logger.info(
                "[{}]: received no data from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )


class OEFHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = OEFMessage.protocol_id  # type: Optional[ProtocolId]

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
        oef_msg = cast(OEFMessage, message)
        if oef_msg.type is OEFMessage.Type.SEARCH_RESULT:
            agents = oef_msg.agents
            self._handle_search(agents)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_search(self, agents: List[str]) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :return: None
        """
        if len(agents) > 0:
            logger.info(
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
            dialogue = dialogues.create_self_initiated(
                opponent_addr, self.context.agent_address, is_seller=False
            )
            query = strategy.get_service_query()
            logger.info(
                "[{}]: sending CFP to agent={}".format(
                    self.context.agent_name, opponent_addr[-5:]
                )
            )
            cfp_msg = FIPAMessage(
                message_id=FIPAMessage.STARTING_MESSAGE_ID,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                performative=FIPAMessage.Performative.CFP,
                target=FIPAMessage.STARTING_TARGET,
                query=query,
            )
            dialogue.outgoing_extend(cfp_msg)
            self.context.outbox.put_message(
                to=opponent_addr,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(cfp_msg),
            )
        else:
            logger.info(
                "[{}]: found no agents, continue searching.".format(
                    self.context.agent_name
                )
            )


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
            logger.info(
                "[{}]: transaction was successful.".format(self.context.agent_name)
            )
            json_data = {"transaction_digest": tx_msg_response.tx_digest}
            info = cast(Dict[str, Any], tx_msg_response.info)
            dialogue_label = DialogueLabel.from_json(
                cast(Dict[str, str], info.get("dialogue_label"))
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogue = dialogues.dialogues[dialogue_label]
            fipa_msg = cast(FIPAMessage, dialogue.last_incoming_message)
            new_message_id = fipa_msg.message_id + 1
            new_target_id = fipa_msg.message_id
            counterparty_addr = dialogue.dialogue_label.dialogue_opponent_addr
            inform_msg = FIPAMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target_id,
                performative=FIPAMessage.Performative.INFORM,
                info=json_data,
            )
            dialogue.outgoing_extend(inform_msg)
            self.context.outbox.put_message(
                to=counterparty_addr,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(inform_msg),
            )
            logger.info(
                "[{}]: informing counterparty={} of transaction digest.".format(
                    self.context.agent_name, counterparty_addr[-5:]
                )
            )
        else:
            logger.info(
                "[{}]: transaction was not successful.".format(self.context.agent_name)
            )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
