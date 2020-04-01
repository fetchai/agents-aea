# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This package contains handlers for the erc1155-client skill."""

from typing import Optional, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.contracts.erc1155.contract import ERC1155Contract
from packages.fetchai.protocols.fipa.dialogues import FipaDialogue
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.fipa.serialization import FipaSerializer
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.erc1155_client.strategy import Strategy


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

        if fipa_msg.performative == FipaMessage.Performative.INFORM:
            self._handle_inform(fipa_msg)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_inform(self, msg: FipaMessage) -> None:
        """
        Handle the match inform.

        :param msg: the message
        :return: None
        """
        self.context.logger.info(
            "[{}]: received INFORM from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        if len(msg.info.keys()) >= 1:
            data = msg.info
            if "contract" in data.keys():
                contract = cast(ERC1155Contract, self.context.contracts.erc1155)
                contract.set_address(
                    ledger_api=self.context.ledger_apis.ethereum_api,
                    contract_address=data["contract"],
                )
                assert "from_supply" in data.keys(), "from supply is not set"
                assert "to_supply" in data.keys(), "to supply is not set"
                assert "value" in data.keys(), "value is not set"
                assert "trade_nonce" in data.keys(), "trade_nonce is not set"
                assert "token_id" in data.keys(), "token id is not set"

                self.counterparty = msg.counterparty
                tx = contract.get_hash_single_transaction(
                    from_address=msg.counterparty,
                    to_address=self.context.agent_address,
                    item_id=cast(int, data["token_id"]),
                    from_supply=cast(int, data["from_supply"]),
                    to_supply=cast(int, data["to_supply"]),
                    value=cast(int, data["value"]),
                    trade_nonce=cast(int, data["trade_nonce"]),
                    ledger_api=self.context.ledger_apis.ethereum_api,
                    skill_callback_id=self.context.skill_id,
                )

                self.context.decision_maker_message_queue.put_nowait(tx)

        else:
            self.context.logger.info(
                "[{}]: received no data from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )


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

            query = strategy.get_service_query()
            self.context.logger.info(
                "[{}]: sending CFP to agent={}".format(
                    self.context.agent_name, opponent_addr[-5:]
                )
            )
            cfp_msg = FipaMessage(
                message_id=FipaDialogue.STARTING_MESSAGE_ID,
                dialogue_reference=("", ""),
                performative=FipaMessage.Performative.CFP,
                target=FipaDialogue.STARTING_TARGET,
                query=query,
            )
            self.context.outbox.put_message(
                to=opponent_addr,
                sender=self.context.agent_address,
                protocol_id=FipaMessage.protocol_id,
                message=FipaSerializer().encode(cfp_msg),
            )
        else:
            self.context.logger.info(
                "[{}]: found no agents, continue searching.".format(
                    self.context.agent_name
                )
            )


class TransactionHandler(Handler):
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
        self.context.logger.info(tx_msg_response)
        if (
            tx_msg_response.tx_id
            == ERC1155Contract.Performative.CONTRACT_SIGN_HASH.value
        ):
            tx_signed = tx_msg_response.signed_payload.get("tx_signature")
            new_message_id = 2
            new_target = 1

            inform_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=("", ""),
                target=new_target,
                performative=FipaMessage.Performative.INFORM,
                info={"signature": tx_signed},
            )
            self.context.outbox.put_message(
                to=self.context.handlers.fipa.counterparty,
                sender=self.context.agent_address,
                protocol_id=FipaMessage.protocol_id,
                message=FipaSerializer().encode(inform_msg),
            )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
