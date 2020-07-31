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

"""This package contains a tac search behaviour."""

from typing import Any, Dict, cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_participation.dialogues import OefSearchDialogues
from packages.fetchai.skills.tac_participation.game import Game, Phase


class TacSearchBehaviour(TickerBehaviour):
    """This class scaffolds a behaviour."""

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        game = cast(Game, self.context.game)
        if game.phase.value == Phase.PRE_GAME.value:
            self._search_for_tac()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass

    def _search_for_tac(self) -> None:
        """
        Search for active TAC Controller.

        We assume that the controller is registered as a service with the 'tac' data model
        and with an attribute version = expected_version_id.

        :return: None
        """
        game = cast(Game, self.context.game)
        query = game.get_game_query()
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
        self.context.logger.info(
            "searching for TAC, search_id={}".format(oef_search_msg.dialogue_reference)
        )


class TransactionProcessBehaviour(TickerBehaviour):
    """This class implements the processing of the transactions class."""

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def act(self) -> None:
        """
        Implement the task execution.

        :return: None
        """
        game = cast(Game, self.context.game)
        if game.phase.value == Phase.GAME.value:
            self._process_transactions()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass

    def _process_transactions(self) -> None:
        """
        Process transactions.

        :return: None
        """
        game = cast(Game, self.context.game)
        tac_dialogue = game.tac_dialogue
        transactions = cast(
            Dict[str, Dict[str, Any]], self.context.shared_state["transactions"]
        )
        for tx_id, tx_content in transactions.items():
            self.context.logger.info(
                "sending transaction {} to controller.".format(tx_id)
            )
            last_msg = tac_dialogue.last_message
            assert last_msg is not None, "No last message available."
            terms = tx_content["terms"]
            sender_signature = tx_content["sender_signature"]
            counterparty_signature = tx_content["counterparty_signature"]
            msg = TacMessage(
                performative=TacMessage.Performative.TRANSACTION,
                dialogue_reference=tac_dialogue.dialogue_label.dialogue_reference,
                message_id=last_msg.message_id + 1,
                target=last_msg.message_id,
                tx_id=tx_id,
                tx_sender_addr=terms.sender_address,
                tx_counterparty_addr=terms.counterparty_address,
                amount_by_currency_id=terms.amount_by_currency_id,
                is_sender_payable_tx_fee=terms.is_sender_payable_tx_fee,
                quantities_by_good_id=terms.quantities_by_good_id,
                tx_sender_signature=sender_signature,
                tx_counterparty_signature=counterparty_signature,
                tx_nonce=terms.nonce,
            )
            msg.counterparty = game.conf.controller_addr
            tac_dialogue.update(msg)
            self.context.outbox.put_message(message=msg)
